"""Tests for the 3ERL integration setup and unload."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.zero_inject_3erl.const import CONF_API_URL, DOMAIN, SERVICE_RESET_COUNTERS

from .conftest import PV_POWER_ENTITY


async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that the entry loads and unloads cleanly."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_select_unique_id_is_migrated(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that the legacy mode select unique id gets the domain prefix."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "select",
        DOMAIN,
        f"{config_entry.entry_id}_mode",
        config_entry=config_entry,
        suggested_object_id="custom_mode",
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = registry.async_get("select.custom_mode")
    assert entity is not None
    assert entity.unique_id == f"{DOMAIN}_{config_entry.entry_id}_mode"
    assert config_entry.minor_version == 2


async def test_reset_counters_service(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that the reset service clears the cumulative counters."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinator
    coordinator._cumulative_energy_kwh = 5.0

    await hass.services.async_call(DOMAIN, SERVICE_RESET_COUNTERS, blocking=True)

    assert coordinator.data["energie_bridage_kwh"] == 0.0


async def test_reset_counters_service_accepts_values(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that optional fields set the counters instead of zeroing them."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinator

    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_COUNTERS,
        {"energy_kwh": 12.5, "gain_eur": 3.75},
        blocking=True,
    )

    assert coordinator.data["energie_bridage_kwh"] == 12.5
    assert coordinator.data["gain_cumule_eur"] == 3.75


async def test_api_url_option_is_used(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that the API URL saved in the options is the one polled."""
    custom_url = "https://example.test/api.json"
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, CONF_API_URL: custom_url}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data.coordinator
    assert coordinator._api_client._api_url == custom_url


async def test_power_updates_do_not_postpone_api_polling(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that frequent PV power changes do not delay the next API poll."""
    hass.states.async_set(PV_POWER_ENTITY, "100")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_fetch.call_count == 1

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    hass.states.async_set(PV_POWER_ENTITY, "200")
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=40))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert mock_fetch.call_count == 2


async def test_unload_stops_power_listener(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that an unloaded coordinator no longer reacts to the PV sensor."""
    hass.states.async_set(PV_POWER_ENTITY, "100")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinator

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator._last_update_time = None
    hass.states.async_set(PV_POWER_ENTITY, "2500")
    await hass.async_block_till_done()

    assert coordinator.data["pv_power_w"] == 100.0
