"""Buttons of Tessera Control: one per page, to show it."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TesseraConfigEntry
from .const import CONF_PAGE, SUBENTRY_PAGE
from .controller import TesseraController
from .entity import TesseraControlEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TesseraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a button for every page."""
    controller = entry.runtime_data
    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type == SUBENTRY_PAGE:
            async_add_entities(
                [PageButton(controller, subentry)], config_subentry_id=subentry_id
            )


class PageButton(TesseraControlEntity, ButtonEntity):
    """Shows its page and pauses the rotation for a while."""

    def __init__(self, controller: TesseraController, subentry: ConfigSubentry) -> None:
        """Create the button for one page."""
        super().__init__(controller, "show_page")
        self._attr_unique_id = f"{controller.entry.entry_id}_{subentry.subentry_id}"
        self._attr_translation_placeholders = {"page_name": subentry.title}
        self._page = int(subentry.data[CONF_PAGE])

    async def async_press(self) -> None:
        """Show the page."""
        await self.controller.async_show_page(self._page)
