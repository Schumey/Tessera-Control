"""Constants of Tessera Control."""

from __future__ import annotations

from typing import Any

DOMAIN = "tessera_control"
ESPHOME_DOMAIN = "esphome"

# Config entry data
CONF_DEVICE_ID = "device_id"
CONF_SHOW_PAGE_SERVICE = "show_page_service"

# Options
CONF_FALLBACK_PAGE = "fallback_page"
CONF_PAUSE_MINUTES = "pause_minutes"
CONF_SLEEP_ENTITY = "sleep_entity"
CONF_PRESENCE_ENTITY = "presence_entity"
CONF_ROOM_LIGHTS = "room_lights"
CONF_SLEEP_SCREEN_OFF = "sleep_screen_off"
CONF_BACK_TO_PAGE_1_OFF = "back_to_page_1_off"
# The brightness level of each situation, 1 to 3
CONF_DAY_LEVEL = "day_level"
CONF_EVENING_LEVEL = "evening_level"
CONF_DARK_LEVEL = "dark_level"
CONF_AWAY_LEVEL = "away_level"
CONF_ASLEEP_LEVEL = "asleep_level"

DEFAULT_OPTIONS: dict[str, Any] = {
    CONF_FALLBACK_PAGE: 1,
    CONF_PAUSE_MINUTES: 5,
    CONF_ROOM_LIGHTS: [],
    CONF_SLEEP_SCREEN_OFF: True,
    CONF_BACK_TO_PAGE_1_OFF: False,
    CONF_DAY_LEVEL: 1,
    CONF_EVENING_LEVEL: 2,
    CONF_DARK_LEVEL: 3,
    CONF_AWAY_LEVEL: 3,
    CONF_ASLEEP_LEVEL: 3,
}

# Page subentries
SUBENTRY_PAGE = "page"
CONF_PAGE = "page"
CONF_PAGE_COUNT = "page_count"
CONF_PAGE_NAME = "name"
CONF_SHOW = "show"
CONF_ENTITY = "entity"
CONF_STATES = "states"
SHOW_ALWAYS = "always"
SHOW_WHEN = "when"
SUGGESTED_STATES = ["on", "home", "playing", "printing", "paused"]

MAX_PAGE = 20

# Brightness levels 1 to 3: number entities, so they can be set on a dashboard
DEFAULT_LEVELS = {1: 100, 2: 60, 3: 20}
MIN_LEVEL = 5  # a level never turns the screen off; sleep does that
# The levels' keys up to 0.4.0, still in the unique IDs of older entries
OLD_LEVEL_KEYS = {"brightness_day": 1, "brightness_evening": 2, "brightness_dim": 3}

# Rotation interval, seconds
DEFAULT_INTERVAL = 30
MIN_INTERVAL = 10
MAX_INTERVAL = 600

# The screen's own entities, by domain and the name Tessera's firmware gives them
SCREEN_BACK_TO_PAGE_1 = "back_to_page_1"
SCREEN_BRIGHTNESS = "brightness"
SCREEN_WAKE = "wake"
SCREEN_SLEEP = "sleep"
SCREEN_ENTITIES: dict[str, tuple[str, str]] = {
    SCREEN_BACK_TO_PAGE_1: ("switch", "Back to page 1"),
    SCREEN_BRIGHTNESS: ("number", "Normal brightness"),
    SCREEN_WAKE: ("button", "Wake"),
    SCREEN_SLEEP: ("button", "Sleep"),
}
