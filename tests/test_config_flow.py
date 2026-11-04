"""Tests of the config flow, the options and the page subentries."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr

from custom_components.tessera_control.const import DOMAIN

from .conftest import SHOW_PAGE, Screen


async def test_user_flow(hass: HomeAssistant, screen: Screen) -> None:
    """Choosing the screen creates the entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device_id": screen.device.id}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Moin!"
    assert result["data"] == {
        "device_id": screen.device.id,
        "show_page_service": SHOW_PAGE,
    }
    assert result["result"].unique_id == screen.device.id
    assert not result["result"].subentries


async def test_user_flow_with_pages(hass: HomeAssistant, screen: Screen) -> None:
    """With the number of pages, setting up adds them all."""
    hass.config.language = "de"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device_id": screen.device.id, "page_count": 3.0}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    pages = sorted(
        (subentry.data["page"], subentry.title, dict(subentry.data))
        for subentry in result["result"].subentries.values()
    )
    assert pages == [
        (1, "Seite 1", {"page": 1, "show": "always"}),
        (2, "Seite 2", {"page": 2, "show": "always"}),
        (3, "Seite 3", {"page": 3, "show": "always"}),
    ]
    assert hass.states.get("button.moin_show_seite_3") is not None


async def test_user_flow_already_configured(hass: HomeAssistant, screen: Screen) -> None:
    """A screen is set up once."""
    await screen.setup_entry()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device_id": screen.device.id}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_screen_offline(hass: HomeAssistant, screen: Screen) -> None:
    """Without the show_page action the screen is offline."""
    hass.services.async_remove("esphome", SHOW_PAGE)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device_id": screen.device.id}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "screen_offline"}


async def test_user_flow_not_tessera(hass: HomeAssistant, screen: Screen) -> None:
    """Another ESPHome device is no Tessera screen."""
    other_entry = MockConfigEntry(domain="esphome", data={"device_name": "plug"})
    other_entry.add_to_hass(hass)
    other = dr.async_get(hass).async_get_or_create(
        config_entry_id=other_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff")},
        name="Plug",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device_id": other.id}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_tessera"}


async def test_options_flow(hass: HomeAssistant, screen: Screen) -> None:
    """The options are stored, numbers as whole numbers."""
    entry = await screen.setup_entry()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "fallback_page": 1.0,
            "pause_minutes": 10.0,
            "sleep_entity": "binary_sensor.sleep",
            "room_lights": ["light.ceiling"],
            "sleep_screen_off": True,
            "back_to_page_1_off": True,
            "day_level": 1.0,
            "evening_level": 2.0,
            "dark_level": 3.0,
            "away_level": 2.0,
            "asleep_level": 3.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["pause_minutes"] == 10
    assert entry.options["fallback_page"] == 1
    assert entry.options["back_to_page_1_off"] is True
    assert entry.options["away_level"] == 2
    assert "presence_entity" not in entry.options


async def test_add_and_change_page(hass: HomeAssistant, screen: Screen) -> None:
    """A page is a subentry with a button of its own."""
    entry = await screen.setup_entry(pages=[])
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "page"), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "page"}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Drucker", "page": 3.0, "show": "when", "entity": "sensor.printer"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "condition_missing"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Drucker",
            "page": 3.0,
            "show": "when",
            "entity": "sensor.printer",
            "states": ["printing", " paused ", ""],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    (subentry,) = entry.subentries.values()
    assert subentry.title == "Drucker"
    assert dict(subentry.data) == {
        "page": 3,
        "show": "when",
        "entity": "sensor.printer",
        "states": ["printing", "paused"],
    }
    assert hass.states.get("button.moin_show_drucker") is not None

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "page"),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Drucker", "page": 4.0, "show": "always"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert dict(entry.subentries[subentry.subentry_id].data) == {
        "page": 4,
        "show": "always",
    }


async def _add_all_pages(hass: HomeAssistant, entry_id: str, count: float) -> dict:
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "page"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "all_pages"}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"page_count": count}
    )


async def test_add_all_pages(hass: HomeAssistant, screen: Screen) -> None:
    """All pages at once leaves the pages already set up as they are."""
    entry = await screen.setup_entry()
    before = {sub.subentry_id: sub for sub in entry.subentries.values()}

    result = await _add_all_pages(hass, entry.entry_id, 5.0)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "pages_added"
    assert result["description_placeholders"] == {"pages": "Page 4, Page 5"}
    await hass.async_block_till_done()

    for subentry_id, subentry in before.items():
        assert entry.subentries[subentry_id] == subentry
    added = sorted(
        (sub.data["page"], sub.title, dict(sub.data))
        for subentry_id, sub in entry.subentries.items()
        if subentry_id not in before
    )
    assert added == [
        (4, "Page 4", {"page": 4, "show": "always"}),
        (5, "Page 5", {"page": 5, "show": "always"}),
    ]
    assert hass.states.get("button.moin_show_page_5") is not None


async def test_add_all_pages_none_new(hass: HomeAssistant, screen: Screen) -> None:
    """When every page is there already, nothing is added."""
    entry = await screen.setup_entry()
    count = len(entry.subentries)
    result = await _add_all_pages(hass, entry.entry_id, 2.0)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_new_pages"
    assert len(entry.subentries) == count
