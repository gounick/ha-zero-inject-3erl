"""Tests for the 3ERL config and options flows."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.api import ThreeERLApiError
from custom_components.zero_inject_3erl.const import (
    CONF_AGGREGATION_MODE,
    CONF_API_URL,
    CONF_NOTIFY_SERVICE,
    CONF_PV_POWER_ENTITY,
    CONF_RELAY_ENTITY,
    DEFAULT_API_URL,
    DOMAIN,
)

from .conftest import PV_POWER_ENTITY, RELAY_ENTITY


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """Test that the user step validates the API and creates the entry."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: DEFAULT_API_URL,
            CONF_AGGREGATION_MODE: "aci",
            CONF_PV_POWER_ENTITY: PV_POWER_ENTITY,
            CONF_RELAY_ENTITY: RELAY_ENTITY,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_RELAY_ENTITY] == RELAY_ENTITY


async def test_user_flow_cannot_connect(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """Test that an unreachable API shows an error."""
    mock_fetch.side_effect = ThreeERLApiError("boom")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: DEFAULT_API_URL,
            CONF_AGGREGATION_MODE: "aci",
            CONF_PV_POWER_ENTITY: PV_POWER_ENTITY,
            CONF_RELAY_ENTITY: RELAY_ENTITY,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow_shows_form(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that opening the options flow displays the form."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_clears_notify_service(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that leaving the notification field empty removes it."""
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_NOTIFY_SERVICE: "notify.phone"}
    )
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: DEFAULT_API_URL,
            CONF_AGGREGATION_MODE: "aci",
            CONF_PV_POWER_ENTITY: PV_POWER_ENTITY,
            CONF_RELAY_ENTITY: RELAY_ENTITY,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_NOTIFY_SERVICE not in config_entry.options
