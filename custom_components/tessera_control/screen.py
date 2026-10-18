"""Find a Tessera screen's action and entities in Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import slugify

from .const import ESPHOME_DOMAIN, SCREEN_BACK_TO_PAGE_1, SCREEN_ENTITIES


@dataclass(frozen=True)
class Screen:
    """What Tessera Control uses of one screen."""

    device_id: str
    show_page_service: str
    back_to_page_1: str | None
    brightness: str | None
    wake: str | None
    sleep: str | None


def show_page_service(hass: HomeAssistant, device: dr.DeviceEntry) -> str | None:
    """The name of the screen's show_page action, as ESPHome registers it.

    ESPHome names a device's actions <node name with _ for ->_<action>.
    """
    if device.config_entry_id is None:
        return None
    entry = hass.config_entries.async_get_entry(device.config_entry_id)
    if entry is None or entry.domain != ESPHOME_DOMAIN:
        return None
    if name := entry.data.get("device_name"):
        return f"{name.replace('-', '_')}_show_page"
    return None


def screen_entities(hass: HomeAssistant, device_id: str) -> dict[str, str | None]:
    """The screen's own entities, found by domain and the name the firmware gives them."""
    entries = er.async_entries_for_device(er.async_get(hass), device_id)
    found: dict[str, str | None] = {}
    for key, (domain, name) in SCREEN_ENTITIES.items():
        suffix = f"_{slugify(name)}"
        found[key] = next(
            (
                entry.entity_id
                for entry in entries
                if entry.domain == domain
                and (entry.original_name == name or entry.entity_id.endswith(suffix))
            ),
            None,
        )
    return found


def resolve_screen(
    hass: HomeAssistant, device_id: str, stored_service: str | None = None
) -> Screen | None:
    """Everything Tessera Control needs of the screen, or None when it is not a Tessera screen."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    service = show_page_service(hass, device) or stored_service
    entities = screen_entities(hass, device_id)
    if service is None or entities[SCREEN_BACK_TO_PAGE_1] is None:
        return None
    return Screen(
        device_id=device_id,
        show_page_service=service,
        **entities,
    )
