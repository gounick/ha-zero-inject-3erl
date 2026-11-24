"""Tests for the configurable duration number entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.const import DOMAIN

from .conftest import RELAY_ENTITY, sample_api_response


def _number_entity_id(hass: HomeAssistant, entry: MockConfigEntry, suffix: str) -> str:
    """Return the number entity id for the given duration suffix."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "number", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{suffix}"
    )
    assert entity_id is not None
    return entity_id


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the config entry."""
    hass.states.async_set(RELAY_ENTITY, "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_duration_numbers_exist_with_defaults(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that both duration numbers exist with their default values."""
    mock_fetch.return_value = sample_api_response(bridage=0)
    await _setup(hass, config_entry)

    bypass_id = _number_entity_id(hass, config_entry, "bypass_duration")
    mode_id = _number_entity_id(hass, config_entry, "forced_mode_duration")
    assert hass.states.get(bypass_id).state == "60"
    assert hass.states.get(mode_id).state == "30"


async def test_duration_number_set_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that the duration numbers accept new values."""
    mock_fetch.return_value = sample_api_response(bridage=0)
    await _setup(hass, config_entry)

    bypass_id = _number_entity_id(hass, config_entry, "bypass_duration")
    await hass.services.async_call(
        "number", "set_value", {"entity_id": bypass_id, "value": 120}, blocking=True
    )
    assert float(hass.states.get(bypass_id).state) == 120
