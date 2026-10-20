"""Tests for the 3ERL binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.zero_inject_3erl.const import DOMAIN


async def test_active_sensor_follows_mode_select(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that the active sensor updates as soon as the mode changes."""
    async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    active_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{DOMAIN}_{config_entry.entry_id}_zero_inject_active"
    )
    mode_id = registry.async_get_entity_id(
        "select", DOMAIN, f"{DOMAIN}_{config_entry.entry_id}_mode"
    )
    assert hass.states.get(active_id).state == "off"

    await hass.services.async_call(
        "select", "select_option", {"entity_id": mode_id, "option": "On"}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get(active_id)
    assert state.state == "on"
    assert state.attributes["mode"] == "On"
