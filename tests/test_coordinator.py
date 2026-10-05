"""Tests for the 3ERL data coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.api import ThreeERLApiClient
from custom_components.zero_inject_3erl.const import (
    CONF_PV_POWER_ENTITY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from custom_components.zero_inject_3erl.coordinator import ThreeERLUpdateCoordinator


def _sample_api_response() -> dict[str, Any]:
    """Return a sample 3ERL API response."""
    return {
        "Bridage": 1,
        "Bridage_CDC": 0,
        "Dernier_PREP": 150.0,
        "Heure_Update": "30/09/2026 15:00",
        "PREP_Profile": "1+",
        "PRD4": 120.0,
        "Bridage_Long_Terme": 0,
    }


@pytest.fixture
def coordinator(hass: HomeAssistant) -> ThreeERLUpdateCoordinator:
    """Return a coordinator instance with a mocked API client."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PV_POWER_ENTITY: "sensor.pv_power",
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_MINUTES,
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)
    api = AsyncMock(spec=ThreeERLApiClient)
    session = AsyncMock()
    return ThreeERLUpdateCoordinator(hass, api, session, entry)


async def test_build_data_no_power(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test computed data when the PV power sensor is unavailable."""
    hass.states.async_set("sensor.pv_power", "unavailable")
    await hass.async_block_till_done()

    data = coordinator._build_data(_sample_api_response())

    assert data["puissance_bridable"] == 0.0
    assert data["puissance_gain"] == 0.0
    assert data["energie_bridage_kwh"] == 0.0
    assert data["gain_cumule_eur"] == 0.0


async def test_build_data_curtailment_active(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test computed data during active curtailment."""
    hass.states.async_set("sensor.pv_power", "2000")
    await hass.async_block_till_done()

    data = coordinator._build_data(_sample_api_response())

    assert data["puissance_bridable"] == 2000.0
    # 2000 W * 150 EUR/MWh * 0.7 / 1_000_000 = 0.21 EUR/h
    assert data["puissance_gain"] == pytest.approx(0.21, rel=1e-4)


async def test_build_data_no_curtailment(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test computed data when curtailment is not requested."""
    hass.states.async_set("sensor.pv_power", "2000")
    await hass.async_block_till_done()

    api_data = {**_sample_api_response(), "Bridage": 0}
    data = coordinator._build_data(api_data)

    assert data["puissance_bridable"] == 0.0
    assert data["puissance_gain"] == 0.0


async def test_accumulate_energy(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test energy and gain accumulation during curtailment."""
    hass.states.async_set("sensor.pv_power", "1000")
    await hass.async_block_till_done()

    now = datetime.now(UTC)
    coordinator._last_update_time = now - timedelta(hours=1)
    coordinator._accumulate_from_power_sensor(now, _sample_api_response())

    # 1000 W * 1 h / 1000 = 1 kWh
    assert coordinator._cumulative_energy_kwh == pytest.approx(1.0, rel=1e-6)
    # 1 kWh * 150 EUR/MWh * 0.7 / 1000 = 0.105 EUR
    assert coordinator._cumulative_gain_eur == pytest.approx(0.105, rel=1e-6)
