"""Tessera Control: page rotation and brightness for a Tessera screen."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_DEVICE_ID, CONF_SHOW_PAGE_SERVICE, DOMAIN, SCREEN_BACK_TO_PAGE_1
from .controller import TesseraController
from .screen import resolve_screen, screen_entities

PLATFORMS = [Platform.BUTTON, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]

type TesseraConfigEntry = ConfigEntry[TesseraController]


async def async_setup_entry(hass: HomeAssistant, entry: TesseraConfigEntry) -> bool:
    """Set up the rotation and brightness of one screen."""
    screen = resolve_screen(
        hass, entry.data[CONF_DEVICE_ID], entry.data.get(CONF_SHOW_PAGE_SERVICE)
    )
    if screen is None:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="screen_missing"
        )

    controller = TesseraController(hass, entry, screen)
    entry.runtime_data = controller
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    controller.async_start()
    entry.async_on_unload(controller.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.async_create_background_task(
        hass, controller.async_begin(), f"{DOMAIN} begin {entry.entry_id}"
    )
    return True


async def _async_update_listener(hass: HomeAssistant, entry: TesseraConfigEntry) -> None:
    """Options or pages changed: start again with them."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: TesseraConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: TesseraConfigEntry) -> None:
    """Give the screen its own "Back to page 1" again."""
    entity = screen_entities(hass, entry.data[CONF_DEVICE_ID])[SCREEN_BACK_TO_PAGE_1]
    state = hass.states.get(entity) if entity else None
    if state is not None and state.state == "off":
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity}, blocking=False
        )
