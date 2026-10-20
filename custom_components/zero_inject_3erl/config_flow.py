"""Config flow for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import (
    AGGREGATION_MODES,
    CONF_AGGREGATION_MODE,
    CONF_API_URL,
    CONF_CONSUMPTION_POWER_ENTITY,
    CONF_NOTIFY_SERVICE,
    CONF_PRD3_DAY_OFFSET,
    CONF_PV_POWER_ENTITY,
    CONF_RELAY_ENTITY,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_API_URL,
    DEFAULT_PRD3_DAY_OFFSET,
    DOMAIN,
)
from .helpers import entity_id_list, pv_power_entities, relay_entities

_LOGGER = logging.getLogger(__name__)

DEFAULT_VALUES: dict[str, Any] = {
    CONF_API_URL: DEFAULT_API_URL,
    CONF_AGGREGATION_MODE: DEFAULT_AGGREGATION_MODE,
    CONF_PRD3_DAY_OFFSET: DEFAULT_PRD3_DAY_OFFSET,
}

SETTINGS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL): str,
        vol.Required(CONF_AGGREGATION_MODE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AGGREGATION_MODES,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key=CONF_AGGREGATION_MODE,
            )
        ),
        vol.Required(CONF_PV_POWER_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="power", multiple=True)
        ),
        vol.Required(CONF_RELAY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch", multiple=True)
        ),
        vol.Optional(CONF_CONSUMPTION_POWER_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="power")
        ),
        vol.Optional(CONF_NOTIFY_SERVICE): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="notify", multiple=True)
        ),
        vol.Optional(CONF_PRD3_DAY_OFFSET): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=-7,
                max=0,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
    }
)


async def _async_validate_api(hass: HomeAssistant, api_url: str) -> dict[str, str]:
    """Check that the 3ERL API answers at the given URL.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param api_url: URL of the 3ERL JSON endpoint.
    :type api_url: str
    :return: Form errors, empty when the API is reachable.
    :rtype: dict[str, str]
    """
    try:
        await ThreeERLApiClient(async_get_clientsession(hass), api_url).fetch()
    except ThreeERLApiError:
        return {"base": "cannot_connect"}
    except Exception:
        _LOGGER.exception("Unexpected exception while validating the 3ERL API")
        return {"base": "unknown"}
    return {}


class ZeroInject3ERLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for 3ERL Zero-Injection."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await _async_validate_api(self.hass, user_input[CONF_API_URL])
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="3ERL Zero-Injection", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                SETTINGS_SCHEMA, user_input or DEFAULT_VALUES
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZeroInject3ERLOptionsFlow:
        """Return the options flow handler."""
        return ZeroInject3ERLOptionsFlow()


class ZeroInject3ERLOptionsFlow(config_entries.OptionsFlow):
    """Options flow for 3ERL Zero-Injection."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await _async_validate_api(self.hass, user_input[CONF_API_URL])
            if not errors:
                return self.async_create_entry(data=user_input)

        current = {**DEFAULT_VALUES, **self.config_entry.data, **self.config_entry.options}
        # Entries created before multi-sensor support store a single entity
        # id string; the selector expects a list.
        current[CONF_PV_POWER_ENTITY] = pv_power_entities(current)
        current[CONF_RELAY_ENTITY] = relay_entities(current)
        current[CONF_NOTIFY_SERVICE] = entity_id_list(current, CONF_NOTIFY_SERVICE)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(SETTINGS_SCHEMA, user_input or current),
            errors=errors,
        )
