"""Base entity of Tessera Control."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .controller import TesseraController


class TesseraControlEntity(Entity):
    """An entity on the screen's own device that follows the controller."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, controller: TesseraController, key: str) -> None:
        """Name the entity after its key."""
        self.controller = controller
        self._attr_translation_key = key
        self._attr_unique_id = f"{controller.entry.entry_id}_{key}"
        # Shown on the screen's own device, which stays ESPHome's
        self.device_entry = dr.async_get(controller.hass).async_get(
            controller.screen.device_id
        )

    async def async_added_to_hass(self) -> None:
        """Follow the controller."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.controller.signal, self._on_update)
        )

    @callback
    def _on_update(self) -> None:
        self.async_write_ha_state()
