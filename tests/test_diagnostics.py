"""Tests for config entry diagnostics."""

from custom_components.zero_inject_3erl.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_config_entry_diagnostics(hass, config_entry, mock_fetch):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

    assert diagnostics["signal"]["curtailment_requested"] is False
    assert diagnostics["signal"]["last_update_success"] is True
    assert diagnostics["pricing"]["last_update_success"] is True
    assert diagnostics["control"]["manual_bypass"] is False
    assert "api_url" in diagnostics["settings"]
