"""Tests for the 3ERL data coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.api import ThreeERLApiClient
from custom_components.zero_inject_3erl.const import (
    CONF_CONSUMPTION_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
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
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)
    api = AsyncMock(spec=ThreeERLApiClient)
    session = AsyncMock()
    return ThreeERLUpdateCoordinator(hass, api, session, entry)


async def test_power_tracking_starts_once(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test that the power listener is registered only once, on demand."""
    assert coordinator._unsub_power is None

    coordinator.start_power_tracking()
    first = coordinator._unsub_power
    assert first is not None

    coordinator.start_power_tracking()
    assert coordinator._unsub_power is first

    await coordinator.async_shutdown()
    assert coordinator._unsub_power is None


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


async def test_accumulate_energy_subtracts_consumption(
    hass: HomeAssistant,
) -> None:
    """Test that the lost surplus subtracts home consumption when configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PV_POWER_ENTITY: "sensor.pv_power",
            CONF_CONSUMPTION_POWER_ENTITY: "sensor.home_power",
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)
    api = AsyncMock(spec=ThreeERLApiClient)
    coordinator = ThreeERLUpdateCoordinator(hass, api, AsyncMock(), entry)

    hass.states.async_set("sensor.pv_power", "1000")
    hass.states.async_set("sensor.home_power", "300")
    await hass.async_block_till_done()

    now = datetime.now(UTC)
    coordinator._last_update_time = now - timedelta(hours=1)
    coordinator._accumulate_from_power_sensor(now, _sample_api_response())

    # (1000 W - 300 W) * 1 h / 1000 = 0.7 kWh
    assert coordinator._cumulative_energy_kwh == pytest.approx(0.7, rel=1e-6)


async def test_multiple_pv_sensors_are_summed(
    hass: HomeAssistant,
) -> None:
    """Test that several production sensors are summed into a single power."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PV_POWER_ENTITY: ["sensor.pv_power_a", "sensor.pv_power_b"],
        },
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)
    api = AsyncMock(spec=ThreeERLApiClient)
    coordinator = ThreeERLUpdateCoordinator(hass, api, AsyncMock(), entry)

    hass.states.async_set("sensor.pv_power_a", "1000")
    hass.states.async_set("sensor.pv_power_b", "500")
    await hass.async_block_till_done()

    now = datetime.now(UTC)
    coordinator._last_update_time = now - timedelta(hours=1)
    coordinator._accumulate_from_power_sensor(now, _sample_api_response())

    # (1000 W + 500 W) * 1 h / 1000 = 1.5 kWh
    assert coordinator._cumulative_energy_kwh == pytest.approx(1.5, rel=1e-6)


async def test_accumulation_attributes_intervals_to_current_signal(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test that each interval is counted under the signal in effect then."""
    hass.states.async_set("sensor.pv_power", "1000")
    await hass.async_block_till_done()

    start = datetime.now(UTC)
    coordinator._last_update_time = start

    active = _sample_api_response()
    inactive = {**_sample_api_response(), "Bridage": 0}

    # 1 h of curtailment counts, the following hour off-signal does not.
    coordinator._accumulate_from_power_sensor(start + timedelta(hours=1), active)
    coordinator._accumulate_from_power_sensor(start + timedelta(hours=2), inactive)

    assert coordinator._cumulative_energy_kwh == pytest.approx(1.0, rel=1e-6)


async def test_old_api_data_is_flagged_stale(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test that data older than two publication cycles is marked stale."""
    api_data = {**_sample_api_response(), "Heure_Update": "01/01/2020 00:00"}

    data = coordinator._build_data(api_data)

    assert data["data_stale"] is True
    assert data["data_age_minutes"] > 30


async def test_fresh_api_data_is_not_stale(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test that a recent Heure_Update is not marked stale."""
    recent = (datetime.now(ZoneInfo("Europe/Paris")) - timedelta(minutes=10)).strftime(
        "%d/%m/%Y %H:%M"
    )
    api_data = {**_sample_api_response(), "Heure_Update": recent}

    data = coordinator._build_data(api_data)

    assert data["data_stale"] is False


async def test_non_watt_power_sensor_logs_a_warning(
    hass: HomeAssistant,
    coordinator: ThreeERLUpdateCoordinator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a sensor in kW is read but reported in the logs."""
    hass.states.async_set("sensor.pv_power", "1.5", attributes={"unit_of_measurement": "kW"})
    await hass.async_block_till_done()

    coordinator._pv_power_w()

    assert "reports kW" in caplog.text


async def test_accumulation_writes_are_batched(
    hass: HomeAssistant, coordinator: ThreeERLUpdateCoordinator
) -> None:
    """Test that accumulation defers disk writes and flushes on shutdown."""
    hass.states.async_set("sensor.pv_power", "1000")
    await hass.async_block_till_done()
    start = datetime.now(UTC)
    coordinator._last_update_time = start

    with patch.object(coordinator._store, "async_save") as save:
        for minute in range(1, 6):
            coordinator._accumulate_from_power_sensor(
                start + timedelta(minutes=minute), _sample_api_response()
            )
        await hass.async_block_till_done()
        save.assert_not_called()

        await coordinator.async_shutdown()

    save.assert_awaited_once()
    assert save.await_args.args[0]["energy_kwh"] == pytest.approx(1000 * 5 / 60 / 1000)
