"""Tests of the decisions in logic.py, which need no Home Assistant."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

# Load logic.py by its path: importing the package would import Home Assistant.
_PATH = Path(__file__).parents[1] / "custom_components" / "tessera_control" / "logic.py"
_SPEC = importlib.util.spec_from_file_location("tessera_control_logic", _PATH)
logic = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = logic  # dataclasses look the module up there
_SPEC.loader.exec_module(logic)

HOME = logic.PageRule(page=1, always=True)
PC = logic.PageRule(page=2, always=False, entity_id="binary_sensor.pc", states=frozenset({"on"}))
PRINTER = logic.PageRule(
    page=3,
    always=False,
    entity_id="sensor.printer",
    states=frozenset({"printing", "paused"}),
)
RULES = [PRINTER, HOME, PC]


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        ({}, [1]),
        ({"binary_sensor.pc": "on"}, [1, 2]),
        ({"binary_sensor.pc": "on", "sensor.printer": "printing"}, [1, 2, 3]),
        ({"binary_sensor.pc": "off", "sensor.printer": "paused"}, [1, 3]),
        ({"binary_sensor.pc": "unavailable", "sensor.printer": "complete"}, [1]),
    ],
)
def test_active_pages(states, expected):
    assert logic.active_pages(RULES, states, fallback=1) == expected


def test_active_pages_fallback_when_nothing_applies():
    assert logic.active_pages([PC], {}, fallback=4) == [4]
    assert logic.active_pages([], {}, fallback=1) == [1]


def test_active_pages_same_page_twice():
    other = logic.PageRule(page=2, always=False, entity_id="light.desk", states=frozenset({"on"}))
    assert logic.active_pages([HOME, PC, other], {"light.desk": "on"}, 1) == [1, 2]


@pytest.mark.parametrize(
    ("pages", "current", "expected"),
    [
        ([1, 2, 3], 1, 2),
        ([1, 2, 3], 3, 1),
        ([1], 1, 1),
        ([1, 2], None, 1),
        ([1, 3], 2, 1),
    ],
)
def test_page_after(pages, current, expected):
    assert logic.page_after(pages, current) == expected


@pytest.mark.parametrize(
    ("before", "after", "current", "expected"),
    [
        ([1, 2], [1, 2, 3], 2, 3),  # the printer starts: its page at once
        ([1], [1, 2, 3], 1, 3),  # two joined: the last one
        ([1, 3], [1], 3, 1),  # the current page left
        ([1, 2, 3], [1, 2], 2, 2),  # another page left: stay
        ([], [1, 2], 2, 2),  # nothing known before: stay
        ([], [1, 2], None, 1),
    ],
)
def test_page_after_change(before, after, current, expected):
    assert logic.page_after_change(before, after, current) == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("on", True),
        ("home", True),
        ("2", True),
        ("0", False),
        ("off", False),
        ("not_home", False),
        ("unavailable", False),
        (None, False),
    ],
)
def test_is_present(state, expected):
    assert logic.is_present(state) is expected


def test_is_lit():
    assert logic.is_lit(["off", "on"]) is True
    assert logic.is_lit(["off", "unavailable"]) is False
    assert logic.is_lit([]) is False


LEVELS = {"day": 100, "evening": 60, "dim": 20}


@pytest.mark.parametrize(
    ("present", "sun_up", "room_lit", "expected"),
    [
        (True, True, False, 100),
        (True, True, True, 100),
        (True, False, True, 60),
        (True, False, False, 20),
        (False, True, True, 20),
        (False, False, True, 20),
    ],
)
def test_target_brightness(present, sun_up, room_lit, expected):
    assert (
        logic.target_brightness(present=present, sun_up=sun_up, room_lit=room_lit, **LEVELS)
        == expected
    )
