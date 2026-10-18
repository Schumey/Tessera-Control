"""Fixtures: a Tessera screen as ESPHome would set it up."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)

from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.tessera_control.const import (
    CONF_DEVICE_ID,
    CONF_SHOW_PAGE_SERVICE,
    DOMAIN,
)

MAC = "b8:1f:3f:aa:56:d8"
SHOW_PAGE = "dsp_desktop_show_page"

PAGES = [
    ConfigSubentryData(
        data={"page": 1, "show": "always"},
        subentry_type="page",
        title="Start",
        unique_id=None,
    ),
    ConfigSubentryData(
        data={"page": 2, "show": "when", "entity": "binary_sensor.pc", "states": ["on"]},
        subentry_type="page",
        title="PC",
        unique_id=None,
    ),
    ConfigSubentryData(
        data={
            "page": 3,
            "show": "when",
            "entity": "sensor.printer",
            "states": ["printing", "paused"],
        },
        subentry_type="page",
        title="Drucker",
        unique_id=None,
    ),
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the integration from custom_components."""


class Screen:
    """A fake Tessera screen and what was asked of it."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Register the screen's device, entities and show_page action."""
        self.hass = hass
        self.esphome_entry = MockConfigEntry(
            domain="esphome", data={"device_name": "dsp-desktop"}, unique_id=MAC
        )
        self.esphome_entry.add_to_hass(hass)
        self.device = dr.async_get(hass).async_get_or_create(
            config_entry_id=self.esphome_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, MAC)},
            name="Moin!",
            manufacturer="maxgramser",
            model="esp_screen",
        )
        registry = er.async_get(hass)
        self.entities: dict[str, str] = {}
        for domain, key, name, state in (
            ("switch", "back_to_page_1", "Back to page 1", "on"),
            ("number", "normal_brightness", "Normal brightness", "100"),
            ("button", "wake", "Wake", "unknown"),
            ("button", "sleep", "Sleep", "unknown"),
        ):
            entry = registry.async_get_or_create(
                domain,
                "esphome",
                f"{MAC}-{domain}-{key}",
                suggested_object_id=f"moin_{key}",
                device_id=self.device.id,
                config_entry=self.esphome_entry,
                original_name=name,
                has_entity_name=True,
            )
            hass.states.async_set(entry.entity_id, state)
            self.entities[key] = entry.entity_id
        self.pages_shown = async_mock_service(hass, "esphome", SHOW_PAGE)
        self.service_calls = async_capture_events(hass, EVENT_CALL_SERVICE)

    def pages(self) -> list[int]:
        """The pages asked for, in order."""
        return [call.data["page"] for call in self.pages_shown]

    def calls(self, domain: str, service: str) -> list[dict[str, Any]]:
        """The service data of every call of one action."""
        return [
            event.data["service_data"]
            for event in self.service_calls
            if event.data["domain"] == domain and event.data["service"] == service
        ]

    async def setup_entry(
        self,
        options: dict[str, Any] | None = None,
        pages: list[ConfigSubentryData] | None = None,
    ) -> MockConfigEntry:
        """Set up Tessera Control for the screen."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Moin!",
            unique_id=self.device.id,
            data={CONF_DEVICE_ID: self.device.id, CONF_SHOW_PAGE_SERVICE: SHOW_PAGE},
            options=options or {},
            subentries_data=PAGES if pages is None else pages,
        )
        entry.add_to_hass(self.hass)
        assert await self.hass.config_entries.async_setup(entry.entry_id)
        await self.hass.async_block_till_done()
        return entry


@pytest.fixture
def screen(hass: HomeAssistant) -> Screen:
    """A Tessera screen with nothing switched on."""
    hass.states.async_set("sun.sun", "above_horizon")
    hass.states.async_set("binary_sensor.pc", "off")
    hass.states.async_set("sensor.printer", "standby")
    return Screen(hass)
