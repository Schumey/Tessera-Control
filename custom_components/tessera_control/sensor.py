"""Sensors of Tessera Control: the current page and the pages in the rotation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TesseraConfigEntry
from .controller import TesseraController
from .entity import TesseraControlEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TesseraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the two sensors."""
    controller = entry.runtime_data
    async_add_entities([CurrentPageSensor(controller), PagesSensor(controller)])


class CurrentPageSensor(TesseraControlEntity, SensorEntity):
    """The page Tessera Control showed last. The screen does not report its page."""

    def __init__(self, controller: TesseraController) -> None:
        """Create the sensor."""
        super().__init__(controller, "current_page")

    @property
    def native_value(self) -> int | None:
        """The page shown last."""
        return self.controller.current_page


class PagesSensor(TesseraControlEntity, SensorEntity):
    """The pages in the rotation now, as "1,2,3"."""

    def __init__(self, controller: TesseraController) -> None:
        """Create the sensor."""
        super().__init__(controller, "pages")

    @property
    def native_value(self) -> str:
        """The pages, comma separated."""
        return ",".join(str(page) for page in self.controller.pages)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """The pages as a list."""
        return {"pages": list(self.controller.pages)}
