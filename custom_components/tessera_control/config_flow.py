"""Config flow of Tessera Control: the screen, its options and its pages."""

from __future__ import annotations

from typing import Any

import probatio as vol

from homeassistant.config_entries import (
    ConfigEntry,
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
    CONF_DEVICE_ID,
    CONF_ENTITY,
    CONF_FALLBACK_PAGE,
    CONF_PAGE,
    CONF_PAGE_NAME,
    CONF_PAUSE_MINUTES,
    CONF_PRESENCE_ENTITY,
    CONF_ROOM_LIGHTS,
    CONF_SHOW,
    CONF_SHOW_PAGE_SERVICE,
    CONF_SLEEP_ENTITY,
    CONF_SLEEP_SCREEN_OFF,
    CONF_STATES,
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
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): DeviceSelector(
                        DeviceSelectorConfig(integration=ESPHOME_DOMAIN)
                    )
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
        vol.Required(CONF_SLEEP_SCREEN_OFF): BooleanSelector(),
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
    """Add or change one page of the rotation."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a page."""
        return await self._async_page_form("user", user_input, None)

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
