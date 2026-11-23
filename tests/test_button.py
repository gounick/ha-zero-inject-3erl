"""Tests for the refresh button."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.const import DOMAIN

from .conftest import RELAY_ENTITY, sample_api_response


async def test_refresh_button_triggers_immediate_poll(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that pressing the refresh button polls the 3ERL API at once."""
    mock_fetch.return_value = sample_api_response(bridage=0)
    hass.states.async_set(RELAY_ENTITY, "off")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    button_id = er.async_get(hass).async_get_entity_id(
        "button", DOMAIN, f"{DOMAIN}_{config_entry.entry_id}_refresh"
    )
    assert button_id is not None

    initial_calls = mock_fetch.call_count
    await hass.services.async_call("button", "press", {"entity_id": button_id}, blocking=True)
    await hass.async_block_till_done()

    assert mock_fetch.call_count == initial_calls + 1
