"""Config flow of Tessera Control: the screen, its options and its pages."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import probatio as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigSubentryData,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.selector import (
    BooleanSelector,
    DeviceSelector,
    DeviceSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_ASLEEP_LEVEL,
    CONF_AWAY_LEVEL,
    CONF_BACK_TO_PAGE_1_OFF,
    CONF_DARK_LEVEL,
    CONF_DAY_LEVEL,
    CONF_DEVICE_ID,
    CONF_ENTITY,
    CONF_EVENING_LEVEL,
    CONF_FALLBACK_PAGE,
    CONF_PAGE,
    CONF_PAGE_COUNT,
    CONF_PAGE_NAME,
    CONF_PAUSE_MINUTES,
    CONF_PRESENCE_ENTITY,
    CONF_ROOM_LIGHTS,
    CONF_SHOW,
    CONF_SHOW_PAGE_SERVICE,
    CONF_SLEEP_ENTITY,
    CONF_SLEEP_SCREEN_OFF,
    CONF_STATES,
    DEFAULT_LEVELS,
    DEFAULT_OPTIONS,
    DOMAIN,
    ESPHOME_DOMAIN,
    MAX_PAGE,
    SHOW_ALWAYS,
    SHOW_WHEN,
    SUBENTRY_PAGE,
    SUGGESTED_STATES,
)
from .screen import resolve_screen

PAGE_NUMBER = NumberSelector(
    NumberSelectorConfig(min=1, max=MAX_PAGE, step=1, mode=NumberSelectorMode.BOX)
)
PAGE_COUNT = NumberSelector(
    NumberSelectorConfig(min=1, max=MAX_PAGE, step=1, mode=NumberSelectorMode.BOX)
)
LEVEL_NUMBER = NumberSelector(
    NumberSelectorConfig(
        min=1, max=len(DEFAULT_LEVELS), step=1, mode=NumberSelectorMode.SLIDER
    )
)


class TesseraControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Choose the screen."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a Tessera screen among the ESPHome devices."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            screen = resolve_screen(self.hass, device_id)
            if screen is None:
                errors["base"] = "not_tessera"
            elif not self.hass.services.has_service(
                ESPHOME_DOMAIN, screen.show_page_service
            ):
                errors["base"] = "screen_offline"
            else:
                device = dr.async_get(self.hass).async_get(device_id)
                title = (device.name_by_user or device.name) if device else None
                return self.async_create_entry(
                    title=title or "Tessera",
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_SHOW_PAGE_SERVICE: screen.show_page_service,
                    },
                    subentries=new_pages(
                        self.hass.config.language,
                        int(user_input.get(CONF_PAGE_COUNT, 0)),
                        set(),
                    ),
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): DeviceSelector(
                        DeviceSelectorConfig(integration=ESPHOME_DOMAIN)
                    ),
                    vol.Optional(CONF_PAGE_COUNT): PAGE_COUNT,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Options: pages, sleep, presence, room lights."""
        return TesseraControlOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Pages are subentries."""
        return {SUBENTRY_PAGE: PageSubentryFlow}


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FALLBACK_PAGE): PAGE_NUMBER,
        vol.Required(CONF_PAUSE_MINUTES): NumberSelector(
            NumberSelectorConfig(
                min=1, max=120, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
            )
        ),
        vol.Optional(CONF_SLEEP_ENTITY): EntitySelector(
            EntitySelectorConfig(domain=["binary_sensor", "input_boolean", "switch"])
        ),
        vol.Optional(CONF_PRESENCE_ENTITY): EntitySelector(
            EntitySelectorConfig(
                domain=[
                    "binary_sensor",
                    "device_tracker",
                    "input_boolean",
                    "person",
                    "zone",
                ]
            )
        ),
        vol.Optional(CONF_ROOM_LIGHTS): EntitySelector(
            EntitySelectorConfig(domain="light", multiple=True)
        ),
        vol.Required(CONF_DAY_LEVEL): LEVEL_NUMBER,
        vol.Required(CONF_EVENING_LEVEL): LEVEL_NUMBER,
        vol.Required(CONF_DARK_LEVEL): LEVEL_NUMBER,
        vol.Required(CONF_AWAY_LEVEL): LEVEL_NUMBER,
        vol.Required(CONF_SLEEP_SCREEN_OFF): BooleanSelector(),
        vol.Required(CONF_ASLEEP_LEVEL): LEVEL_NUMBER,
        vol.Required(CONF_BACK_TO_PAGE_1_OFF): BooleanSelector(),
    }
)


class TesseraControlOptionsFlow(OptionsFlow):
    """Change what the rotation and the brightness depend on."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """One form with every option."""
        if user_input is not None:
            options = {
                key: int(value) if isinstance(value, float) else value
                for key, value in user_input.items()
            }
            return self.async_create_entry(data=options)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, {**DEFAULT_OPTIONS, **self.config_entry.options}
            ),
        )


def page_title(language: str, page: int) -> str:
    """The name a page gets when it is added with all the others."""
    word = "Seite" if language.split("-")[0] == "de" else "Page"
    return f"{word} {page}"


def new_pages(language: str, count: int, existing: set[int]) -> list[ConfigSubentryData]:
    """Pages 1 to count that are not among the existing page numbers, each always in the rotation."""
    return [
        ConfigSubentryData(
            data={CONF_PAGE: page, CONF_SHOW: SHOW_ALWAYS},
            subentry_type=SUBENTRY_PAGE,
            title=page_title(language, page),
            unique_id=None,
        )
        for page in range(1, count + 1)
        if page not in existing
    ]


def _page_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PAGE_NAME): TextSelector(),
            vol.Required(CONF_PAGE): PAGE_NUMBER,
            vol.Required(CONF_SHOW, default=SHOW_ALWAYS): SelectSelector(
                SelectSelectorConfig(
                    options=[SHOW_ALWAYS, SHOW_WHEN],
                    mode=SelectSelectorMode.LIST,
                    translation_key="show",
                )
            ),
            vol.Optional(CONF_ENTITY): EntitySelector(),
            vol.Optional(CONF_STATES): SelectSelector(
                SelectSelectorConfig(
                    options=SUGGESTED_STATES,
                    multiple=True,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class PageSubentryFlow(ConfigSubentryFlow):
    """Add one page or all of them, or change one page of the rotation."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """One page, or all pages at once."""
        return self.async_show_menu(step_id="user", menu_options=["page", "all_pages"])

    async def async_step_page(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a page."""
        return await self._async_page_form("page", user_input, None)

    async def async_step_all_pages(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add pages 1 to the screen's last, leaving out the pages already there."""
        if user_input is not None:
            entry = self._get_entry()
            existing = {
                int(subentry.data[CONF_PAGE])
                for subentry in entry.subentries.values()
                if subentry.subentry_type == SUBENTRY_PAGE
            }
            pages = new_pages(
                self.hass.config.language, int(user_input[CONF_PAGE_COUNT]), existing
            )
            if not pages:
                return self.async_abort(reason="no_new_pages")
            for page in pages:
                self.hass.config_entries.async_add_subentry(
                    entry,
                    ConfigSubentry(
                        data=MappingProxyType(page["data"]),
                        subentry_type=page["subentry_type"],
                        title=page["title"],
                        unique_id=page["unique_id"],
                    ),
                )
            return self.async_abort(
                reason="pages_added",
                description_placeholders={
                    "pages": ", ".join(page["title"] for page in pages)
                },
            )
        return self.async_show_form(
            step_id="all_pages",
            data_schema=vol.Schema({vol.Required(CONF_PAGE_COUNT): PAGE_COUNT}),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change a page."""
        return await self._async_page_form(
            "reconfigure", user_input, self._get_reconfigure_subentry()
        )

    async def _async_page_form(
        self,
        step_id: str,
        user_input: dict[str, Any] | None,
        subentry: ConfigSubentry | None,
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            states = [
                state.strip() for state in user_input.get(CONF_STATES, []) if state.strip()
            ]
            entity = user_input.get(CONF_ENTITY)
            if user_input[CONF_SHOW] == SHOW_WHEN and not (entity and states):
                errors["base"] = "condition_missing"
            else:
                data: dict[str, Any] = {
                    CONF_PAGE: int(user_input[CONF_PAGE]),
                    CONF_SHOW: user_input[CONF_SHOW],
                }
                if user_input[CONF_SHOW] == SHOW_WHEN:
                    data[CONF_ENTITY] = entity
                    data[CONF_STATES] = states
                title = user_input[CONF_PAGE_NAME].strip()
                if subentry is None:
                    return self.async_create_entry(title=title, data=data)
                return self.async_update_and_abort(
                    self._get_entry(), subentry, title=title, data=data
                )

        suggested: dict[str, Any] = dict(user_input or {})
        if subentry is not None and user_input is None:
            suggested = {CONF_PAGE_NAME: subentry.title, **subentry.data}
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(_page_schema(), suggested),
            errors=errors,
        )
