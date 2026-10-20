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

DEFAULT_OPTIONS: dict[str, Any] = {
    CONF_FALLBACK_PAGE: 1,
    CONF_PAUSE_MINUTES: 5,
    CONF_ROOM_LIGHTS: [],
    CONF_SLEEP_SCREEN_OFF: True,
    CONF_BACK_TO_PAGE_1_OFF: False,
}

# Page subentries
SUBENTRY_PAGE = "page"
CONF_PAGE = "page"
CONF_PAGE_NAME = "name"
CONF_SHOW = "show"
CONF_ENTITY = "entity"
CONF_STATES = "states"
SHOW_ALWAYS = "always"
SHOW_WHEN = "when"
SUGGESTED_STATES = ["on", "home", "playing", "printing", "paused"]

MAX_PAGE = 20

# Brightness levels: number entities, so they can be set on a dashboard
LEVEL_DAY = "brightness_day"
LEVEL_EVENING = "brightness_evening"
LEVEL_DIM = "brightness_dim"
DEFAULT_LEVELS = {LEVEL_DAY: 100, LEVEL_EVENING: 60, LEVEL_DIM: 20}
MIN_LEVEL = 5  # a level never turns the screen off; sleep does that

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
