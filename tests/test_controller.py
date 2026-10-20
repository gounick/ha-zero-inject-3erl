"""Tests for the zero-injection relay controller."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant, ServiceCall, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
    mock_restore_cache,
)

from custom_components.zero_inject_3erl.const import (
    CONF_NOTIFY_SERVICE,
    CONF_RELAY_ENTITY,
    DOMAIN,
)

from .conftest import RELAY_ENTITY, sample_api_response

NOTIFY_ENTITY = "notify.phone"


def _mode_entity_id(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    """Return the mode select entity id of the given entry."""
    entity_id = er.async_get(hass).async_get_entity_id(
        "select", DOMAIN, f"{DOMAIN}_{entry.entry_id}_mode"
    )
    assert entity_id is not None
    return entity_id


async def _select_mode(hass: HomeAssistant, entry: MockConfigEntry, option: str) -> None:
    """Select a zero-injection mode through the select service."""
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": _mode_entity_id(hass, entry), "option": option},
        blocking=True,
    )
    await hass.async_block_till_done()


@pytest.fixture
def turn_on_calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Mock the switch.turn_on service."""
    return async_mock_service(hass, "switch", "turn_on")


@pytest.fixture
def turn_off_calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Mock the switch.turn_off service."""
    return async_mock_service(hass, "switch", "turn_off")


async def test_mode_is_restored_after_restart(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that a forced mode survives a restart."""
    entity_id = f"select.{DOMAIN}_mode"
    er.async_get(hass).async_get_or_create(
        "select",
        DOMAIN,
        f"{DOMAIN}_{config_entry.entry_id}_mode",
        config_entry=config_entry,
        suggested_object_id=f"{DOMAIN}_mode",
    )
    mock_restore_cache(hass, [State(entity_id, "Off")])

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "Off"


async def _setup_with_notify(hass: HomeAssistant, entry: MockConfigEntry) -> list[ServiceCall]:
    """Set up the entry with a notify entity and return the notify calls."""
    notify_calls = async_mock_service(hass, "notify", "send_message")
    hass.config_entries.async_update_entry(
        entry, options={**entry.data, CONF_NOTIFY_SERVICE: NOTIFY_ENTITY}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return notify_calls


async def test_no_notification_on_startup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that startup applies the relay state without notifying."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "off")

    notify_calls = await _setup_with_notify(hass, config_entry)

    assert len(turn_on_calls) == 1
    assert notify_calls == []


async def test_relay_realigned_when_out_of_sync(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that a relay in the wrong state is corrected, then retried."""
    hass.states.async_set(RELAY_ENTITY, "off")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert turn_off_calls == []

    hass.states.async_set(RELAY_ENTITY, "on")
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 1

    coordinator = config_entry.runtime_data.coordinator
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 2


async def test_relay_retried_when_available_again(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that the relay is driven once it becomes available again."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "unavailable")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert turn_on_calls == []

    hass.states.async_set(RELAY_ENTITY, "off")
    await hass.async_block_till_done()

    assert len(turn_on_calls) == 1


async def test_multiple_relays_are_all_driven(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that every configured relay is aligned with the computed state."""
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.config_entries.async_update_entry(
        config_entry,
        options={
            **config_entry.data,
            CONF_RELAY_ENTITY: ["switch.relay_a", "switch.relay_b"],
        },
    )
    hass.states.async_set("switch.relay_a", "off")
    hass.states.async_set("switch.relay_b", "off")

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    called = {call.data["entity_id"] for call in turn_on_calls}
    assert called == {"switch.relay_a", "switch.relay_b"}


async def test_notification_uses_notify_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    turn_on_calls: list[ServiceCall],
    turn_off_calls: list[ServiceCall],
) -> None:
    """Test that notifications target the configured notify entity."""
    hass.states.async_set(RELAY_ENTITY, "off")
    notify_calls = await _setup_with_notify(hass, config_entry)

    await _select_mode(hass, config_entry, "On")

    assert notify_calls[-1].data["entity_id"] == NOTIFY_ENTITY
    assert "ACTIVE" in notify_calls[-1].data["message"]
    assert turn_on_calls[-1].data["entity_id"] == RELAY_ENTITY
