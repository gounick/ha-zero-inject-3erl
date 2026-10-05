"""Config flow for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import (
    AGGREGATION_MODES,
    CONF_AGGREGATION_MODE,
    CONF_API_URL,
    CONF_NOTIFY_SERVICE,
    CONF_PRD3_DAY_OFFSET,
    CONF_PV_POWER_ENTITY,
    CONF_PV_SYSTEM_TYPE,
    CONF_RELAY_ENTITY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_API_URL,
    DEFAULT_PRD3_DAY_OFFSET,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    PV_SYSTEM_GENERIC,
    PV_SYSTEM_TYPES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Required(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_MINUTES
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=60,
                unit_of_measurement="minutes",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Required(CONF_PV_SYSTEM_TYPE, default=PV_SYSTEM_GENERIC): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=PV_SYSTEM_TYPES,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_AGGREGATION_MODE, default=DEFAULT_AGGREGATION_MODE
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AGGREGATION_MODES,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key=CONF_AGGREGATION_MODE,
            )
        ),
        vol.Required(CONF_PV_POWER_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor",
                device_class="power",
            )
        ),
        vol.Required(CONF_RELAY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="switch",
            )
        ),
        vol.Optional(CONF_NOTIFY_SERVICE): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="notify",
            )
        ),
        vol.Optional(
            CONF_PRD3_DAY_OFFSET,
            default=DEFAULT_PRD3_DAY_OFFSET,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=-7,
                max=0,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
    }
)


class ZeroInject3ERLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for 3ERL Zero-Injection."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL]
            session = async_get_clientsession(self.hass)
            try:
                api = ThreeERLApiClient(session, api_url)
                await api.fetch()
            except ThreeERLApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="3ERL Zero-Injection",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> ZeroInject3ERLOptionsFlow:
        """Return the options flow handler."""
        return ZeroInject3ERLOptionsFlow(config_entry)


class ZeroInject3ERLOptionsFlow(config_entries.OptionsFlow):
    """Options flow for 3ERL Zero-Injection."""

    def __init__(self, config_entry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the options step."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_API_URL, default=current.get(CONF_API_URL, DEFAULT_API_URL)): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=current.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_AGGREGATION_MODE,
                    default=current.get(CONF_AGGREGATION_MODE, DEFAULT_AGGREGATION_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=AGGREGATION_MODES,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key=CONF_AGGREGATION_MODE,
                    )
                ),
                vol.Required(
                    CONF_PV_POWER_ENTITY,
                    default=current.get(CONF_PV_POWER_ENTITY),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="power",
                    )
                ),
                vol.Required(
                    CONF_RELAY_ENTITY,
                    default=current.get(CONF_RELAY_ENTITY),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="switch",
                    )
                ),
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    default=current.get(CONF_NOTIFY_SERVICE),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="notify",
                    )
                ),
                vol.Optional(
                    CONF_PRD3_DAY_OFFSET,
                    default=current.get(CONF_PRD3_DAY_OFFSET, DEFAULT_PRD3_DAY_OFFSET),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-7,
                        max=0,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
