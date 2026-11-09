"""Tests for the 3ERL integration setup and unload."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.zero_inject_3erl.const import CONF_API_URL, DOMAIN

from .conftest import RELAY_ENTITY, sample_api_response


async def test_control_starts_while_pricing_is_blocked(hass, config_entry, mock_fetch):
    release = asyncio.Event()
    started = asyncio.Event()

    async def blocked_pricing(self):
        started.set()
        await release.wait()

    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "off")
    calls = async_mock_service(hass, "switch", "turn_on")
    with patch(
        "custom_components.zero_inject_3erl.pricing.PricingDataManager.async_update",
        new=blocked_pricing,
    ):
        setup = hass.async_create_task(hass.config_entries.async_setup(config_entry.entry_id))
        await started.wait()
        await asyncio.wait({setup}, timeout=0.2)
        try:
            assert setup.done()
            await hass.async_block_till_done()
            assert len(calls) == 1
        finally:
            release.set()
            await setup
            await hass.async_block_till_done()


async def test_no_energy_service_or_sensor(hass, config_entry, mock_fetch):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert not hass.services.has_service(DOMAIN, "reset_counters")
    assert not any(
        state.attributes.get("device_class") == "energy" for state in hass.states.async_all()
    )


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
    hass.config_entries.async_update_entry(
        config_entry,
        data={**config_entry.data, "pv_power_entity": "sensor.pv"},
        options={**config_entry.data, "consumption_power_entity": "sensor.load"},
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    entity = registry.async_get("select.custom_mode")
    assert entity.unique_id == f"{DOMAIN}_{config_entry.entry_id}_mode"
    assert config_entry.minor_version == 3
    assert "pv_power_entity" not in config_entry.data
    assert "consumption_power_entity" not in config_entry.options


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
    assert config_entry.runtime_data.coordinator._api_client._api_url == custom_url


async def test_local_freshness_updates_do_not_postpone_polling(
    hass, config_entry, mock_fetch, freezer
):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_fetch.call_count == 1
    freezer.tick(timedelta(seconds=70))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_fetch.call_count == 2


async def test_unload_cancels_blocked_pricing(hass, config_entry, mock_fetch):
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def blocked_pricing(self):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    with patch(
        "custom_components.zero_inject_3erl.pricing.PricingDataManager.async_update",
        new=blocked_pricing,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await started.wait()
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        assert cancelled.is_set()
