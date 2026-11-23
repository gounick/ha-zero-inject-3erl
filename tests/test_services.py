"""Tests for the set_bypass service."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.zero_inject_3erl.const import DOMAIN

from .conftest import RELAY_ENTITY, sample_api_response


@pytest.fixture
def relay_commands(hass: HomeAssistant) -> list[str]:
    """Record switch domain service calls targeting the relay entity."""
    commands: list[str] = []

    def _record(event: Event) -> None:
        data = event.data
        if data["domain"] == "switch" and RELAY_ENTITY in str(
            data["service_data"].get("entity_id")
        ):
            commands.append(data["service"])

    hass.bus.async_listen("call_service", _record)
    return commands


def _bypass_entity_id(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    """Return the manual bypass switch entity id of the given entry."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{DOMAIN}_{entry.entry_id}_manual_bypass"
    )
    assert entity_id is not None
    return entity_id


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the config entry with a curtailment demand."""
    hass.states.async_set(RELAY_ENTITY, "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_set_bypass_service_registered_and_removed_on_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that set_bypass is registered on setup and removed on unload."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    await _setup(hass, config_entry)
    assert hass.services.has_service(DOMAIN, "set_bypass")

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert not hass.services.has_service(DOMAIN, "set_bypass")


async def test_set_bypass_enables_bypass_and_suspends_control(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    relay_commands: list[str],
) -> None:
    """Test that enabling the bypass suspends relay control."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    await _setup(hass, config_entry)
    assert relay_commands == ["turn_on"]

    await hass.services.async_call(DOMAIN, "set_bypass", {}, blocking=True)
    await hass.async_block_till_done()

    bypass_id = _bypass_entity_id(hass, config_entry)
    assert hass.states.is_state(bypass_id, "on")
    # The bypass suspends control: the relay is left in its current state.
    assert relay_commands == ["turn_on"]


async def test_set_bypass_with_duration_expires(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that a timed bypass turns itself off after the duration."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    await _setup(hass, config_entry)

    await hass.services.async_call(DOMAIN, "set_bypass", {"duration": 1}, blocking=True)
    await hass.async_block_till_done()
    bypass_id = _bypass_entity_id(hass, config_entry)
    assert hass.states.is_state(bypass_id, "on")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=1, seconds=5))
    await hass.async_block_till_done()
    assert hass.states.is_state(bypass_id, "off")


async def test_set_bypass_disable_cancels_pending_timer(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that disabling the bypass cancels a pending expiry."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    await _setup(hass, config_entry)

    await hass.services.async_call(DOMAIN, "set_bypass", {"duration": 1}, blocking=True)
    await hass.services.async_call(DOMAIN, "set_bypass", {"enable": False}, blocking=True)
    await hass.async_block_till_done()
    bypass_id = _bypass_entity_id(hass, config_entry)
    assert hass.states.is_state(bypass_id, "off")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=2))
    await hass.async_block_till_done()
    assert hass.states.is_state(bypass_id, "off")


async def test_manual_bypass_off_cancels_pending_timer(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
) -> None:
    """Test that turning the switch off manually cancels a pending expiry."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    await _setup(hass, config_entry)

    await hass.services.async_call(DOMAIN, "set_bypass", {"duration": 1}, blocking=True)
    bypass_id = _bypass_entity_id(hass, config_entry)
    assert hass.states.is_state(bypass_id, "on")

    await hass.services.async_call("switch", "turn_off", {"entity_id": bypass_id}, blocking=True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=2))
    await hass.async_block_till_done()
    assert hass.states.is_state(bypass_id, "off")
