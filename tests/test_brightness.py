"""Tests of the automatic brightness."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import mock_restore_cache_with_extra_data

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from custom_components.tessera_control.const import DOMAIN

from .conftest import Screen

SWITCH = "switch.moin_automatic_brightness"
OPTIONS = {
    "presence_entity": "input_boolean.home",
    "sleep_entity": "binary_sensor.sleep",
    "room_lights": ["light.ceiling", "light.desk"],
}


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


def _levels(screen: Screen) -> list[int]:
    brightness = screen.entities["normal_brightness"]
    return [
        data["value"]
        for data in screen.calls("number", "set_value")
        if data["entity_id"] == brightness
    ]


def _presses(screen: Screen) -> list[str]:
    names = {entity: key for key, entity in screen.entities.items()}
    return [names[data["entity_id"]] for data in screen.calls("button", "press")]


async def test_brightness_follows_situation(hass: HomeAssistant, screen: Screen) -> None:
    """Day, evening, dark, away, asleep."""
    hass.states.async_set("input_boolean.home", "on")
    hass.states.async_set("binary_sensor.sleep", "off")
    hass.states.async_set("light.ceiling", "off")
    hass.states.async_set("light.desk", "unavailable")
    await screen.setup_entry(options=OPTIONS)

    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _presses(screen) == ["wake"]
    assert _levels(screen) == []  # day: the screen is at 100 already

    await _set(hass, "sun.sun", "below_horizon")
    assert _levels(screen) == [20]  # every room light off

    await _set(hass, "light.desk", "on")
    assert _levels(screen) == [20, 60]

    await _set(hass, "input_boolean.home", "off")
    assert _levels(screen) == [20, 60, 20]

    await _set(hass, "binary_sensor.sleep", "on")
    assert _presses(screen) == ["wake", "sleep"]

    await _set(hass, "binary_sensor.sleep", "off")
    assert _presses(screen) == ["wake", "sleep", "wake"]


async def test_attribute_changes_are_ignored(hass: HomeAssistant, screen: Screen) -> None:
    """The sun moving all day sets nothing."""
    await screen.setup_entry(options=OPTIONS)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    before = len(screen.service_calls)
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 30})
    await hass.async_block_till_done()
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 31})
    await hass.async_block_till_done()
    assert len(screen.service_calls) == before


async def test_off_sets_nothing(hass: HomeAssistant, screen: Screen) -> None:
    """With the switch off, nothing is set."""
    await screen.setup_entry(options=OPTIONS)
    await _set(hass, "sun.sun", "below_horizon")
    assert _levels(screen) == []
    assert _presses(screen) == []


async def test_dark_level_instead_of_off(hass: HomeAssistant, screen: Screen) -> None:
    """With "screen off while asleep" off, sleep means the dark level."""
    hass.states.async_set("binary_sensor.sleep", "on")
    await screen.setup_entry(options={**OPTIONS, "sleep_screen_off": False})
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _presses(screen) == ["wake"]
    assert _levels(screen) == [20]


async def test_level_applies_at_once(hass: HomeAssistant, screen: Screen) -> None:
    """A new level is set on the screen as soon as it changes."""
    hass.states.async_set("input_boolean.home", "on")
    hass.states.async_set("sun.sun", "below_horizon")
    hass.states.async_set("light.ceiling", "on")
    await screen.setup_entry(options=OPTIONS)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _levels(screen) == [60]

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.moin_brightness_level_2", "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("number.moin_brightness_level_2").state == "40"
    assert _levels(screen)[-1] == 40


async def test_situations_pick_their_level(hass: HomeAssistant, screen: Screen) -> None:
    """Each situation gets the level the options give it.

    The fake screen stays at 100 %, so level 1 would set nothing.
    """
    hass.states.async_set("input_boolean.home", "on")
    hass.states.async_set("binary_sensor.sleep", "off")
    hass.states.async_set("light.ceiling", "off")
    await screen.setup_entry(
        options={
            **OPTIONS,
            "sleep_screen_off": False,
            "day_level": 2,
            "evening_level": 2,
            "dark_level": 3,
            "away_level": 2,
            "asleep_level": 3,
        }
    )
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _levels(screen) == [60]  # day: level 2

    await _set(hass, "sun.sun", "below_horizon")
    assert _levels(screen) == [60, 20]  # dark room: level 3

    await _set(hass, "input_boolean.home", "off")
    assert _levels(screen) == [60, 20, 60]  # away: level 2

    await _set(hass, "binary_sensor.sleep", "on")
    assert _levels(screen) == [60, 20, 60, 20]  # asleep: level 3


async def test_old_levels_keep_entity_ids(hass: HomeAssistant, screen: Screen) -> None:
    """The day, evening and dim levels of 0.4.0 become levels 1 to 3, entity ID and value kept."""
    entry = screen.add_entry()
    old = er.async_get(hass).async_get_or_create(
        "number",
        DOMAIN,
        f"{entry.entry_id}_brightness_evening",
        suggested_object_id="moin_brightness_evening",
        config_entry=entry,
    )
    restored = {
        "native_value": 45,
        "native_min_value": 5,
        "native_max_value": 100,
        "native_step": 5,
        "native_unit_of_measurement": "%",
    }
    mock_restore_cache_with_extra_data(hass, [(State(old.entity_id, "45"), restored)])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert er.async_get(hass).async_get_entity_id(
        "number", DOMAIN, f"{entry.entry_id}_level_2"
    ) == old.entity_id
    assert hass.states.get(old.entity_id).state == "45"
    assert entry.runtime_data.levels[2] == 45
