"""Tests for the 3ERL sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.const import DOMAIN

from .conftest import sample_api_response


def _state(hass: HomeAssistant, entry: MockConfigEntry, key: str):
    """Return the state of the sensor with the given unique id suffix."""
    unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None
    return hass.states.get(entity_id)


async def test_sensor_classes_are_valid(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_fetch: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that sensors use units and state classes accepted by HA."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    gain = _state(hass, config_entry, "gain_cumule_eur")
    assert gain.attributes["unit_of_measurement"] == "EUR"
    assert gain.attributes["state_class"] == "total"
    assert gain.attributes["device_class"] == "monetary"

    price = _state(hass, config_entry, "Dernier_PREP")
    assert price.attributes["unit_of_measurement"] == "€/MWh"
    assert price.attributes["state_class"] == "measurement"
    assert "device_class" not in price.attributes

    assert "impossible considering device class" not in caplog.text
    assert "is using native unit of measurement" not in caplog.text


async def test_sensor_names_are_translated(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test that entity names come from the translation files."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    price = _state(hass, config_entry, "Dernier_PREP")
    assert price.attributes["friendly_name"] == "3ERL Zero-Injection Latest PRE+"


async def test_prep_profile_num_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_fetch: AsyncMock
) -> None:
    """Test the sensor exposing the 3ERL PRD3-weighted daily PRE+."""
    mock_fetch.return_value = {**sample_api_response(), "PREP_Profile_Num": 5.3}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = _state(hass, config_entry, "PREP_Profile_Num")
    assert state.state == "5.3"
    assert state.attributes["unit_of_measurement"] == "€/MWh"
