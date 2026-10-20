"""Tests of the page rotation, the page buttons and the entities."""

from __future__ import annotations

from datetime import timedelta

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    mock_restore_cache,
)

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from .conftest import Screen

ROTATION = "switch.moin_page_rotation"
INTERVAL = "number.moin_rotation_interval"
PAGES = "sensor.moin_pages_in_rotation"
CURRENT = "sensor.moin_current_page"


async def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def _turn(hass: HomeAssistant, entity_id: str, on: bool) -> None:
    await hass.services.async_call(
        "switch", "turn_on" if on else "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()


async def test_entities_after_setup(hass: HomeAssistant, screen: Screen) -> None:
    """Everything is there and off; nothing is asked of the screen."""
    entry = await screen.setup_entry()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(ROTATION).state == "off"
    assert hass.states.get("switch.moin_automatic_brightness").state == "off"
    assert hass.states.get(INTERVAL).state == "30"
    assert hass.states.get("number.moin_brightness_day").state == "100"
    assert hass.states.get("number.moin_brightness_evening").state == "60"
    assert hass.states.get("number.moin_brightness_dim").state == "20"
    assert hass.states.get(PAGES).state == "1"
    assert hass.states.get(PAGES).attributes["pages"] == [1]
    for name in ("start", "pc", "drucker"):
        assert hass.states.get(f"button.moin_show_{name}") is not None
    assert screen.pages() == []


async def test_rotation(hass: HomeAssistant, screen: Screen) -> None:
    """The rotation follows the pages that apply and the timer."""
    await screen.setup_entry()
    back_to_page_1 = screen.entities["back_to_page_1"]

    await _turn(hass, ROTATION, True)
    assert screen.pages() == [1]
    assert {"entity_id": back_to_page_1} in screen.calls("switch", "turn_off")

    # The PC is switched on: its page joins and shows at once
    hass.states.async_set("binary_sensor.pc", "on")
    await hass.async_block_till_done()
    assert screen.pages() == [1, 2]
    assert hass.states.get(PAGES).state == "1,2"
    assert hass.states.get(CURRENT).state == "2"

    # The timer ends: the next page, round and round
    await _later(hass, 31)
    assert screen.pages() == [1, 2, 1]
    await _later(hass, 31)
    assert screen.pages() == [1, 2, 1, 2]

    # The printer starts, then stops while its page shows
    hass.states.async_set("sensor.printer", "printing")
    await hass.async_block_till_done()
    assert screen.pages()[-1] == 3
    hass.states.async_set("sensor.printer", "complete")
    await hass.async_block_till_done()
    assert screen.pages()[-1] == 1

    # Off: the screen gets its "Back to page 1" again
    hass.states.async_set(back_to_page_1, "off")
    await _turn(hass, ROTATION, False)
    assert {"entity_id": back_to_page_1} in screen.calls("switch", "turn_on")
    shown = len(screen.pages())
    await _later(hass, 120)
    assert len(screen.pages()) == shown


async def test_single_page_is_not_sent_again(hass: HomeAssistant, screen: Screen) -> None:
    """With one page the timer runs, but nothing is sent to the screen."""
    await screen.setup_entry()
    await _turn(hass, ROTATION, True)
    await _later(hass, 31)
    await _later(hass, 31)
    assert screen.pages() == [1]


async def test_interval(hass: HomeAssistant, screen: Screen) -> None:
    """A new interval counts from the next page on."""
    hass.states.async_set("binary_sensor.pc", "on")
    await screen.setup_entry()
    await hass.services.async_call(
        "number", "set_value", {"entity_id": INTERVAL, "value": 60}, blocking=True
    )
    await _turn(hass, ROTATION, True)
    assert screen.pages() == [1]
    await _later(hass, 31)
    assert screen.pages() == [1]
    await _later(hass, 61)
    assert screen.pages() == [1, 2]


async def test_page_button_pauses_rotation(hass: HomeAssistant, screen: Screen) -> None:
    """A page button shows its page and holds it for the pause."""
    hass.states.async_set("binary_sensor.pc", "on")
    await screen.setup_entry(options={"pause_minutes": 5})
    await _turn(hass, ROTATION, True)
    assert screen.pages() == [1]

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.moin_show_drucker"}, blocking=True
    )
    await hass.async_block_till_done()
    assert screen.pages() == [1, 3]

    await _later(hass, 31)
    assert screen.pages() == [1, 3]
    await _later(hass, 5 * 60 + 1)
    # Page 3 is not in the rotation (the printer is idle): on to the first page
    assert screen.pages() == [1, 3, 1]


async def test_sleep_pauses_rotation(hass: HomeAssistant, screen: Screen) -> None:
    """While the sleep entity is on, the rotation rests."""
    hass.states.async_set("binary_sensor.pc", "on")
    hass.states.async_set("binary_sensor.sleep", "off")
    await screen.setup_entry(options={"sleep_entity": "binary_sensor.sleep"})
    await _turn(hass, ROTATION, True)
    assert screen.pages() == [1]

    hass.states.async_set("binary_sensor.sleep", "on")
    await hass.async_block_till_done()
    await _later(hass, 31)
    await _later(hass, 31)
    assert screen.pages() == [1]

    hass.states.async_set("binary_sensor.sleep", "off")
    await hass.async_block_till_done()
    assert screen.pages() == [1, 1]
    await _later(hass, 31)
    assert screen.pages() == [1, 1, 2]


async def test_restored_rotation_starts(hass: HomeAssistant, screen: Screen) -> None:
    """After a restart the rotation goes on by itself."""
    mock_restore_cache(hass, [State(ROTATION, "on")])
    await screen.setup_entry()
    assert hass.states.get(ROTATION).state == "on"
    assert screen.pages() == [1]


async def test_offline_screen_comes_back(hass: HomeAssistant, screen: Screen) -> None:
    """A screen that was offline gets its page again when it is back."""
    back_to_page_1 = screen.entities["back_to_page_1"]
    await screen.setup_entry()
    await _turn(hass, ROTATION, True)
    assert screen.pages() == [1]

    hass.states.async_set(back_to_page_1, "unavailable")
    await hass.async_block_till_done()
    hass.states.async_set(back_to_page_1, "on")
    await hass.async_block_till_done()
    assert screen.pages() == [1, 1]


async def test_unload(hass: HomeAssistant, screen: Screen) -> None:
    """After unloading, the timer is gone."""
    hass.states.async_set("binary_sensor.pc", "on")
    entry = await screen.setup_entry()
    await _turn(hass, ROTATION, True)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await _later(hass, 31)
    assert screen.pages() == [1]


async def test_back_to_page_1_kept_off(hass: HomeAssistant, screen: Screen) -> None:
    """With the option, "Back to page 1" stays off, also without the rotation."""
    back_to_page_1 = screen.entities["back_to_page_1"]
    await screen.setup_entry(options={"back_to_page_1_off": True})
    assert screen.calls("switch", "turn_off") == [{"entity_id": back_to_page_1}]
    hass.states.async_set(back_to_page_1, "off")

    # A firmware update: the screen restarts with "Back to page 1" on
    hass.states.async_set(back_to_page_1, "unavailable")
    await hass.async_block_till_done()
    hass.states.async_set(back_to_page_1, "on")
    await hass.async_block_till_done()
    assert len(screen.calls("switch", "turn_off")) == 2
    assert screen.pages() == []

    # The rotation stops: "Back to page 1" is not turned on
    hass.states.async_set(back_to_page_1, "off")
    await _turn(hass, ROTATION, True)
    await _turn(hass, ROTATION, False)
    assert {"entity_id": back_to_page_1} not in screen.calls("switch", "turn_on")


async def test_back_to_page_1_off_while_rotating(hass: HomeAssistant, screen: Screen) -> None:
    """While the rotation runs, "Back to page 1" turned on is turned off again."""
    back_to_page_1 = screen.entities["back_to_page_1"]
    await screen.setup_entry()
    await _turn(hass, ROTATION, True)
    hass.states.async_set(back_to_page_1, "off")
    turned_off = len(screen.calls("switch", "turn_off"))

    hass.states.async_set(back_to_page_1, "on")
    await hass.async_block_till_done()
    assert len(screen.calls("switch", "turn_off")) == turned_off + 1


async def test_back_to_page_1_left_alone(hass: HomeAssistant, screen: Screen) -> None:
    """Without the option and without the rotation, "Back to page 1" is the screen's."""
    back_to_page_1 = screen.entities["back_to_page_1"]
    await screen.setup_entry()
    hass.states.async_set(back_to_page_1, "unavailable")
    await hass.async_block_till_done()
    hass.states.async_set(back_to_page_1, "on")
    await hass.async_block_till_done()
    assert screen.calls("switch", "turn_off") == []
