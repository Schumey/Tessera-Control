"""Numbers of Tessera Control: the rotation interval and the three brightness levels."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TesseraConfigEntry
from .const import (
    DEFAULT_INTERVAL,
    DEFAULT_LEVELS,
    LEVEL_DAY,
    LEVEL_DIM,
    LEVEL_EVENING,
    MAX_INTERVAL,
    MIN_INTERVAL,
    MIN_LEVEL,
)
from .controller import TesseraController
from .entity import TesseraControlEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TesseraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the interval and the levels."""
    controller = entry.runtime_data
    async_add_entities(
        [
            IntervalNumber(controller),
            *(LevelNumber(controller, level) for level in (LEVEL_DAY, LEVEL_EVENING, LEVEL_DIM)),
        ]
    )


class _RestoredNumber(TesseraControlEntity, RestoreNumber):
    """A number that comes back as it was; its default the first time."""

    _attr_entity_category = EntityCategory.CONFIG

    def _default(self) -> int:
        raise NotImplementedError

    def _restore(self, value: int) -> None:
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Restore the last value."""
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        value = last.native_value if last is not None else None
        if value is not None and self.native_min_value <= value <= self.native_max_value:
            self._restore(int(value))
        else:
            self._restore(self._default())


class IntervalNumber(_RestoredNumber):
    """Seconds between two pages."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = MIN_INTERVAL
    _attr_native_max_value = MAX_INTERVAL
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, controller: TesseraController) -> None:
        """Create the number."""
        super().__init__(controller, "rotation_interval")

    def _default(self) -> int:
        return DEFAULT_INTERVAL

    def _restore(self, value: int) -> None:
        self.controller.interval = value

    @property
    def native_value(self) -> float:
        """The interval in seconds."""
        return self.controller.interval

    async def async_set_native_value(self, value: float) -> None:
        """Set a new interval."""
        await self.controller.async_set_interval(int(value))


class LevelNumber(_RestoredNumber):
    """One brightness level: day, evening or dim."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = MIN_LEVEL
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, controller: TesseraController, level: str) -> None:
        """Create the number for one level."""
        super().__init__(controller, level)
        self._level = level

    def _default(self) -> int:
        return DEFAULT_LEVELS[self._level]

    def _restore(self, value: int) -> None:
        self.controller.levels[self._level] = value

    @property
    def native_value(self) -> float:
        """The level in percent."""
        return self.controller.levels[self._level]

    async def async_set_native_value(self, value: float) -> None:
        """Set the level; it applies at once."""
        await self.controller.async_set_level(self._level, int(value))
