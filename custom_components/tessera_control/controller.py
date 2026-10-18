"""The rotation and brightness of one Tessera screen."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_ENTITY,
    CONF_FALLBACK_PAGE,
    CONF_PAGE,
    CONF_PAUSE_MINUTES,
    CONF_PRESENCE_ENTITY,
    CONF_ROOM_LIGHTS,
    CONF_SHOW,
    CONF_SLEEP_ENTITY,
    CONF_SLEEP_SCREEN_OFF,
    CONF_STATES,
    DEFAULT_INTERVAL,
    DEFAULT_LEVELS,
    DEFAULT_OPTIONS,
    DOMAIN,
    ESPHOME_DOMAIN,
    LEVEL_DAY,
    LEVEL_DIM,
    LEVEL_EVENING,
    SHOW_ALWAYS,
    SUBENTRY_PAGE,
)
from .logic import (
    PageRule,
    active_pages,
    is_lit,
    is_present,
    page_after,
    page_after_change,
    target_brightness,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .screen import Screen

_LOGGER = logging.getLogger(__name__)

SUN = "sun.sun"
NOT_THERE = (None, STATE_UNAVAILABLE, STATE_UNKNOWN)

# Why the rotation runs
NEXT = "next"  # the timer ended
CHANGED = "changed"  # the list of pages changed
RESTART = "restart"  # switched on, woke up, the screen came back


class TesseraController:
    """Rotates a screen through its pages and sets its brightness."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, screen: Screen) -> None:
        """Read the entry's options and pages."""
        self.hass = hass
        self.entry = entry
        self.screen = screen
        self.signal = f"{DOMAIN}_{entry.entry_id}_update"

        options = {**DEFAULT_OPTIONS, **entry.options}
        self.fallback_page = int(options[CONF_FALLBACK_PAGE])
        self.pause_minutes = int(options[CONF_PAUSE_MINUTES])
        self.sleep_entity: str | None = options.get(CONF_SLEEP_ENTITY)
        self.presence_entity: str | None = options.get(CONF_PRESENCE_ENTITY)
        self.room_lights: list[str] = list(options[CONF_ROOM_LIGHTS])
        self.sleep_screen_off = bool(options[CONF_SLEEP_SCREEN_OFF])

        self.rules = [
            PageRule(
                page=int(sub.data[CONF_PAGE]),
                always=sub.data[CONF_SHOW] == SHOW_ALWAYS,
                entity_id=sub.data.get(CONF_ENTITY),
                states=frozenset(sub.data.get(CONF_STATES, [])),
            )
            for sub in entry.subentries.values()
            if sub.subentry_type == SUBENTRY_PAGE
        ]

        # Set by the switches and the numbers when they restore their state
        self.rotation_on = False
        self.brightness_on = False
        self.interval = DEFAULT_INTERVAL
        self.levels: dict[str, int] = dict(DEFAULT_LEVELS)

        self.current_page: int | None = None
        self.pages: list[int] = [self.fallback_page]

        self._rotation_lock = asyncio.Lock()
        self._brightness_lock = asyncio.Lock()
        self._cancel_timer: Callable[[], None] | None = None
        self._unsubscribe: list[Callable[[], None]] = []
        self._was_sleeping: bool | None = None

    # Life

    @callback
    def async_start(self) -> None:
        """Listen to everything the rotation and the brightness depend on."""
        self.pages = self._compute_pages()
        screen_entities = {
            entity
            for entity in (self.screen.back_to_page_1, self.screen.brightness)
            if entity
        }
        rotation_entities = {rule.entity_id for rule in self.rules if rule.entity_id}
        brightness_entities = {SUN, *self.room_lights}
        for entity in (self.sleep_entity, self.presence_entity):
            if entity:
                brightness_entities.add(entity)
        if self.sleep_entity:
            rotation_entities.add(self.sleep_entity)

        self._unsubscribe = [
            async_track_state_change_event(
                self.hass, sorted(screen_entities), self._on_screen_change
            ),
            async_track_state_change_event(
                self.hass, sorted(rotation_entities), self._on_rotation_change
            ),
            async_track_state_change_event(
                self.hass, sorted(brightness_entities), self._on_brightness_change
            ),
        ]

    async def async_begin(self) -> None:
        """Apply the restored switches once everything is set up."""
        if self.rotation_on:
            await self._set_back_to_page_1(on=False)
            await self._rotate(RESTART)
        if self.brightness_on:
            await self._apply_brightness()

    @callback
    def async_stop(self) -> None:
        """Stop listening and stop the timer."""
        self._cancel()
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe = []

    # What the entities ask for

    async def async_set_rotation(self, on: bool) -> None:
        """Switch the rotation on or off; off gives the screen its "Back to page 1"."""
        self.rotation_on = on
        self._notify()
        if on:
            await self._set_back_to_page_1(on=False)
            await self._rotate(RESTART)
        else:
            self._cancel()
            await self._set_back_to_page_1(on=True)

    async def async_set_interval(self, seconds: int) -> None:
        """Change the seconds between two pages, from the next page on."""
        self.interval = seconds
        self._notify()
        if self.rotation_on and self._cancel_timer is not None:
            self._schedule(seconds)

    async def async_set_brightness(self, on: bool) -> None:
        """Switch the automatic brightness on or off."""
        self.brightness_on = on
        self._was_sleeping = None
        self._notify()
        if on:
            await self._apply_brightness()

    async def async_set_level(self, level: str, value: int) -> None:
        """Change one brightness level; it applies at once."""
        self.levels[level] = value
        self._notify()
        if self.brightness_on:
            await self._apply_brightness()

    async def async_show_page(self, page: int) -> None:
        """Show a page now and pause the rotation for a while (a button on a dashboard)."""
        async with self._rotation_lock:
            await self._show(page)
        self._notify()
        if self.rotation_on and not self.sleeping:
            self._schedule(self.pause_minutes * 60)

    # State

    @property
    def sleeping(self) -> bool:
        """The sleep entity is on."""
        return bool(self.sleep_entity) and self._state(self.sleep_entity) == "on"

    def _state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def _compute_pages(self) -> list[int]:
        states = {
            rule.entity_id: self._state(rule.entity_id)
            for rule in self.rules
            if rule.entity_id
        }
        return active_pages(self.rules, states, self.fallback_page)

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self.hass, self.signal)

    def _run(self, job: Coroutine[Any, Any, None]) -> None:
        self.entry.async_create_background_task(self.hass, job, f"{DOMAIN} {self.entry.entry_id}")

    # Events

    @callback
    def _on_rotation_change(self, event: Event[EventStateChangedData]) -> None:
        before = self.pages
        self.pages = self._compute_pages()
        if self.pages != before:
            self._notify()
        if event.data["entity_id"] == self.sleep_entity:
            self._run(self._rotate(RESTART))
        elif self.pages != before:
            self._run(self._rotate(CHANGED, before))

    @callback
    def _on_brightness_change(self, event: Event[EventStateChangedData]) -> None:
        old, new = event.data["old_state"], event.data["new_state"]
        if old is not None and new is not None and old.state == new.state:
            return  # only an attribute changed (the sun moves all day)
        if self.brightness_on:
            self._run(self._apply_brightness())

    @callback
    def _on_screen_change(self, event: Event[EventStateChangedData]) -> None:
        """The screen came back after it was offline: show its page and brightness again."""
        old, new = event.data["old_state"], event.data["new_state"]
        if new is None or new.state in NOT_THERE:
            return
        if old is not None and old.state not in NOT_THERE:
            return
        if self.rotation_on and event.data["entity_id"] == self.screen.back_to_page_1:
            self._run(self._resume_rotation())
        if self.brightness_on and event.data["entity_id"] == self.screen.brightness:
            self._was_sleeping = None
            self._run(self._apply_brightness())

    async def _resume_rotation(self) -> None:
        await self._set_back_to_page_1(on=False)
        await self._rotate(RESTART)

    # Rotation

    async def _rotate(self, reason: str, before: list[int] | None = None) -> None:
        async with self._rotation_lock:
            if not self.rotation_on:
                return
            if self.sleeping:
                self._cancel()
                return
            self.pages = self._compute_pages()
            if reason == NEXT:
                target = page_after(self.pages, self.current_page)
            elif reason == CHANGED:
                target = page_after_change(before or [], self.pages, self.current_page)
            else:
                target = (
                    self.current_page
                    if self.current_page in self.pages
                    else self.pages[0]
                )
            if target != self.current_page or reason != NEXT:
                await self._show(target)
            self._schedule(self.interval)
        self._notify()

    def _schedule(self, delay: float) -> None:
        self._cancel()
        self._cancel_timer = async_call_later(self.hass, delay, self._on_timer)

    def _cancel(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

    @callback
    def _on_timer(self, _now: datetime) -> None:
        self._cancel_timer = None
        self._run(self._rotate(NEXT))

    async def _show(self, page: int) -> None:
        """Ask the screen for a page. An offline screen is no error: it misses the page."""
        self.current_page = page
        service = self.screen.show_page_service
        if not self.hass.services.has_service(ESPHOME_DOMAIN, service):
            _LOGGER.debug("Screen offline, page %s not shown", page)
            return
        try:
            await self.hass.services.async_call(
                ESPHOME_DOMAIN, service, {"page": page}, blocking=True
            )
        except HomeAssistantError as err:
            _LOGGER.debug("Page %s not shown: %s", page, err)

    async def _set_back_to_page_1(self, on: bool) -> None:
        entity = self.screen.back_to_page_1
        if entity is None:
            return
        state = self._state(entity)
        if state in NOT_THERE or state == ("on" if on else "off"):
            return
        await self._call("switch", "turn_on" if on else "turn_off", entity)

    # Brightness

    async def _apply_brightness(self) -> None:
        async with self._brightness_lock:
            if not self.brightness_on:
                return
            sleeping = self.sleeping
            was_sleeping, self._was_sleeping = self._was_sleeping, sleeping
            if sleeping and self.sleep_screen_off:
                if was_sleeping is not True and self.screen.sleep:
                    await self._call("button", "press", self.screen.sleep)
                return
            if was_sleeping is not False and self.screen.wake:
                await self._call("button", "press", self.screen.wake)
            if sleeping:
                level = self.levels[LEVEL_DIM]
            else:
                level = target_brightness(
                    present=self.presence_entity is None
                    or is_present(self._state(self.presence_entity)),
                    sun_up=self._state(SUN) != "below_horizon",
                    room_lit=not self.room_lights
                    or is_lit(self._state(light) for light in self.room_lights),
                    day=self.levels[LEVEL_DAY],
                    evening=self.levels[LEVEL_EVENING],
                    dim=self.levels[LEVEL_DIM],
                )
            await self._set_brightness(level)

    async def _set_brightness(self, level: int) -> None:
        entity = self.screen.brightness
        if entity is None:
            return
        state = self._state(entity)
        if state in NOT_THERE:
            return
        try:
            if float(state) == level:
                return
        except ValueError:
            pass
        await self._call("number", "set_value", entity, {"value": level})

    async def _call(
        self,
        domain: str,
        service: str,
        entity_id: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        try:
            await self.hass.services.async_call(
                domain,
                service,
                {"entity_id": entity_id, **(data or {})},
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.debug("%s.%s on %s failed: %s", domain, service, entity_id, err)
