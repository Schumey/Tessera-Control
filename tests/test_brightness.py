"""Tests of the automatic brightness."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import Screen

SWITCH = "switch.moin_automatic_brightness"
OPTIONS = {
    "presence_entity": "input_boolean.home",
    "sleep_entity": "binary_sensor.sleep",
    "room_lights": ["light.ceiling", "light.desk"],
}


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


def _levels(screen: Screen) -> list[int]:
    brightness = screen.entities["normal_brightness"]
    return [
        data["value"]
        for data in screen.calls("number", "set_value")
        if data["entity_id"] == brightness
    ]


def _presses(screen: Screen) -> list[str]:
    names = {entity: key for key, entity in screen.entities.items()}
    return [names[data["entity_id"]] for data in screen.calls("button", "press")]


async def test_brightness_follows_situation(hass: HomeAssistant, screen: Screen) -> None:
    """Day, evening, dark, away, asleep."""
    hass.states.async_set("input_boolean.home", "on")
    hass.states.async_set("binary_sensor.sleep", "off")
    hass.states.async_set("light.ceiling", "off")
    hass.states.async_set("light.desk", "unavailable")
    await screen.setup_entry(options=OPTIONS)

    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _presses(screen) == ["wake"]
    assert _levels(screen) == []  # day: the screen is at 100 already

    await _set(hass, "sun.sun", "below_horizon")
    assert _levels(screen) == [20]  # every room light off

    await _set(hass, "light.desk", "on")
    assert _levels(screen) == [20, 60]

    await _set(hass, "input_boolean.home", "off")
    assert _levels(screen) == [20, 60, 20]

    await _set(hass, "binary_sensor.sleep", "on")
    assert _presses(screen) == ["wake", "sleep"]

    await _set(hass, "binary_sensor.sleep", "off")
    assert _presses(screen) == ["wake", "sleep", "wake"]


async def test_attribute_changes_are_ignored(hass: HomeAssistant, screen: Screen) -> None:
    """The sun moving all day sets nothing."""
    await screen.setup_entry(options=OPTIONS)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    before = len(screen.service_calls)
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 30})
    await hass.async_block_till_done()
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 31})
    await hass.async_block_till_done()
    assert len(screen.service_calls) == before


async def test_off_sets_nothing(hass: HomeAssistant, screen: Screen) -> None:
    """With the switch off, nothing is set."""
    await screen.setup_entry(options=OPTIONS)
    await _set(hass, "sun.sun", "below_horizon")
    assert _levels(screen) == []
    assert _presses(screen) == []


async def test_dark_level_instead_of_off(hass: HomeAssistant, screen: Screen) -> None:
    """With "screen off while asleep" off, sleep means the dark level."""
    hass.states.async_set("binary_sensor.sleep", "on")
    await screen.setup_entry(options={**OPTIONS, "sleep_screen_off": False})
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _presses(screen) == ["wake"]
    assert _levels(screen) == [20]


async def test_level_applies_at_once(hass: HomeAssistant, screen: Screen) -> None:
    """A new level is set on the screen as soon as it changes."""
    hass.states.async_set("sun.sun", "below_horizon")
    hass.states.async_set("light.ceiling", "on")
    await screen.setup_entry(options=OPTIONS)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    assert _levels(screen) == [60]

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.moin_brightness_evening", "value": 40},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("number.moin_brightness_evening").state == "40"
    assert _levels(screen)[-1] == 40
