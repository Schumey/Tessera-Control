"""Switches of Tessera Control: page rotation and automatic brightness."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import TesseraConfigEntry
from .controller import TesseraController
from .entity import TesseraControlEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TesseraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the two switches."""
    controller = entry.runtime_data
    async_add_entities([RotationSwitch(controller), BrightnessSwitch(controller)])


class _RestoredSwitch(TesseraControlEntity, SwitchEntity, RestoreEntity):
    """A switch that comes back as it was; off the first time."""

    _attr_entity_category = EntityCategory.CONFIG

    def _restore(self, on: bool) -> None:
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Restore the last state; the controller applies it once all is set up."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        self._restore(last is not None and last.state == "on")


class RotationSwitch(_RestoredSwitch):
    """Page rotation on or off."""

    def __init__(self, controller: TesseraController) -> None:
        """Create the switch."""
        super().__init__(controller, "rotation")

    def _restore(self, on: bool) -> None:
        self.controller.rotation_on = on

    @property
    def is_on(self) -> bool:
        """The rotation runs."""
        return self.controller.rotation_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the rotation."""
        await self.controller.async_set_rotation(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the rotation."""
        await self.controller.async_set_rotation(False)


class BrightnessSwitch(_RestoredSwitch):
    """Automatic brightness on or off."""

    def __init__(self, controller: TesseraController) -> None:
        """Create the switch."""
        super().__init__(controller, "auto_brightness")

    def _restore(self, on: bool) -> None:
        self.controller.brightness_on = on

    @property
    def is_on(self) -> bool:
        """The brightness follows the situation."""
        return self.controller.brightness_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the automatic brightness."""
        await self.controller.async_set_brightness(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the automatic brightness; the screen keeps its last brightness."""
        await self.controller.async_set_brightness(False)
