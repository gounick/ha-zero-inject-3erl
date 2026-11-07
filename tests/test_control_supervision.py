from datetime import timedelta

import pytest
from homeassistant.core import State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
    mock_restore_cache,
)

from custom_components.zero_inject_3erl.api import ThreeERLApiError
from custom_components.zero_inject_3erl.const import DOMAIN

from .conftest import RELAY_ENTITY, sample_api_response


def entity_id(hass, entry, domain, key):
    result = er.async_get(hass).async_get_entity_id(
        domain, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{key}"
    )
    assert result is not None
    return result


async def setup(hass, entry):
    calls = async_mock_service(hass, "switch", "turn_on")
    async_mock_service(hass, "switch", "turn_off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return calls


async def tick(hass, freezer, seconds):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


@pytest.mark.parametrize("contract", ["aci", "acc"])
async def test_contract_visibility(hass, config_entry, mock_fetch, contract):
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "aggregation_mode": contract}
    )
    await setup(hass, config_entry)
    registry = er.async_get(hass)
    for domain, key, expected_contract in (
        ("binary_sensor", "Bridage", "aci"),
        ("binary_sensor", "Bridage_CDC", "acc"),
        ("sensor", "current_prep", "acc"),
        ("sensor", "estimated_daily_prep", "aci"),
        ("sensor", "PREP_Profile_Num", "aci"),
    ):
        item = registry.async_get(entity_id(hass, config_entry, domain, key))
        assert (item.hidden_by is not None) == (contract != expected_contract)
        assert item.disabled_by is None


async def test_visibility_reload_preserves_user_override(hass, config_entry, mock_fetch):
    await setup(hass, config_entry)
    registry = er.async_get(hass)
    price_id = entity_id(hass, config_entry, "sensor", "current_prep")
    assert registry.async_get(price_id).hidden_by is er.RegistryEntryHider.INTEGRATION
    registry.async_update_entity(price_id, hidden_by=None)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(price_id).hidden_by is None
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "aggregation_mode": "acc"}
    )
    await hass.async_block_till_done()
    assert registry.async_get(price_id).hidden_by is None
    assert registry.async_get(entity_id(hass, config_entry, "binary_sensor", "Bridage")).hidden_by


async def test_bypass_releases_relay_and_resumes_current_signal(hass, config_entry, mock_fetch):
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "on")
    calls = await setup(hass, config_entry)
    bypass_id = entity_id(hass, config_entry, "switch", "manual_bypass")
    await hass.data["switch"].get_entity(bypass_id).async_turn_on()
    await hass.async_block_till_done()
    calls.clear()
    hass.states.async_set(RELAY_ENTITY, "off")
    coordinator = config_entry.runtime_data.coordinator
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()
    assert calls == []
    assert (
        hass.states.get(
            entity_id(hass, config_entry, "binary_sensor", "commanded_limitation")
        ).state
        == "off"
    )
    await hass.data["switch"].get_entity(bypass_id).async_turn_off()
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_bypass_restored_during_api_outage(hass, config_entry, mock_fetch):
    registry = er.async_get(hass)
    item = registry.async_get_or_create(
        "switch",
        DOMAIN,
        f"{DOMAIN}_{config_entry.entry_id}_manual_bypass",
        config_entry=config_entry,
        suggested_object_id="manual_bypass",
    )
    mock_restore_cache(hass, [State(item.entity_id, "on")])
    mock_fetch.side_effect = ThreeERLApiError("offline")
    hass.states.async_set(RELAY_ENTITY, "off")
    calls = await setup(hass, config_entry)
    assert hass.states.get(item.entity_id).state == "on"
    hass.states.async_set(RELAY_ENTITY, "on")
    await hass.async_block_till_done()
    assert calls == []
    assert await hass.config_entries.async_unload(config_entry.entry_id)


async def test_relay_fault_delayed_and_unavailability_immediate(
    hass, config_entry, mock_fetch, freezer
):
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "off")
    await setup(hass, config_entry)
    fault_id = entity_id(hass, config_entry, "binary_sensor", "relay_control_fault")
    assert hass.states.get(fault_id).state == "off"
    await tick(hass, freezer, 31)
    assert hass.states.get(fault_id).state == "on"
    assert hass.states.get(fault_id).attributes["misaligned_relays"] == [RELAY_ENTITY]
    hass.states.async_set(RELAY_ENTITY, "on")
    await hass.async_block_till_done()
    assert hass.states.get(fault_id).state == "off"
    hass.states.async_set(RELAY_ENTITY, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(fault_id).state == "on"
    assert hass.states.get(fault_id).attributes["unavailable_relays"] == [RELAY_ENTITY]


@pytest.mark.parametrize("unit,value", [("W", "100"), ("kW", "0.1"), ("VA", "100"), ("kVA", "0.1")])
async def test_injection_observation_delayed(hass, config_entry, mock_fetch, freezer, unit, value):
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "injection_power_entity": "sensor.export"}
    )
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "on")
    hass.states.async_set("sensor.export", value, {"unit_of_measurement": unit})
    await setup(hass, config_entry)
    injection_id = entity_id(hass, config_entry, "binary_sensor", "injection_during_limitation")
    assert hass.states.get(injection_id).state == "off"
    await tick(hass, freezer, 121)
    assert hass.states.get(injection_id).state == "on"
    hass.states.async_set("sensor.export", "0", {"unit_of_measurement": unit})
    await hass.async_block_till_done()
    assert hass.states.get(injection_id).state == "off"
    await tick(hass, freezer, 301)
    assert hass.states.get(injection_id).state == "unknown"


@pytest.mark.parametrize(
    "value,unit", [("unavailable", "W"), ("nan", "W"), ("inf", "W"), ("10", "kWh"), ("-10", "W")]
)
async def test_invalid_injection_is_not_no_export(hass, config_entry, mock_fetch, value, unit):
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "injection_power_entity": "sensor.export"}
    )
    hass.states.async_set("sensor.export", value, {"unit_of_measurement": unit})
    await setup(hass, config_entry)
    assert (
        hass.states.get(
            entity_id(hass, config_entry, "binary_sensor", "injection_during_limitation")
        ).state
        == "unknown"
    )


async def test_signal_ends_before_relay_returns(hass, config_entry, mock_fetch):
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "unavailable")
    calls = await setup(hass, config_entry)
    coordinator = config_entry.runtime_data.coordinator
    coordinator.async_set_updated_data({**coordinator.data, "api_data": sample_api_response()})
    hass.states.async_set(RELAY_ENTITY, "off")
    await hass.async_block_till_done()
    assert calls == []


async def test_bypass_switch_service_works_without_api(hass, config_entry, mock_fetch):
    mock_fetch.side_effect = ThreeERLApiError("offline")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    bypass_id = entity_id(hass, config_entry, "switch", "manual_bypass")
    assert hass.states.get(bypass_id).state == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": bypass_id}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_id).state == "on"
    assert config_entry.runtime_data.controller.bypassed
    await hass.services.async_call("switch", "turn_off", {"entity_id": bypass_id}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_id).state == "off"
    active_id = entity_id(hass, config_entry, "binary_sensor", "commanded_limitation")
    assert hass.states.get(active_id).state == "unknown"


async def test_bypass_overrides_forced_mode(hass, config_entry, mock_fetch):
    hass.states.async_set(RELAY_ENTITY, "off")
    calls = await setup(hass, config_entry)
    bypass = hass.data["switch"].get_entity(
        entity_id(hass, config_entry, "switch", "manual_bypass")
    )
    await bypass.async_turn_on()
    await hass.async_block_till_done()
    mode_id = entity_id(hass, config_entry, "select", "mode")
    await hass.services.async_call(
        "select", "select_option", {"entity_id": mode_id, "option": "On"}, blocking=True
    )
    await hass.async_block_till_done()
    assert calls == []
    await bypass.async_turn_off()
    await hass.async_block_till_done()
    assert len(calls) == 1


async def test_only_failed_relay_is_reported(hass, config_entry, mock_fetch, freezer):
    hass.config_entries.async_update_entry(
        config_entry,
        options={**config_entry.data, "relay_entity": [RELAY_ENTITY, "switch.other"]},
    )
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "on")
    hass.states.async_set("switch.other", "off")
    await setup(hass, config_entry)
    await tick(hass, freezer, 31)
    state = hass.states.get(entity_id(hass, config_entry, "binary_sensor", "relay_control_fault"))
    assert state.state == "on"
    assert state.attributes["misaligned_relays"] == ["switch.other"]
    bypass = hass.data["switch"].get_entity(
        entity_id(hass, config_entry, "switch", "manual_bypass")
    )
    await bypass.async_turn_on()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id(hass, config_entry, "binary_sensor", "relay_control_fault"))
    assert state.state == "off"
    assert state.attributes["misaligned_relays"] == []


async def test_injection_delay_resets_when_command_ends(hass, config_entry, mock_fetch, freezer):
    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.data, "injection_power_entity": "sensor.export"}
    )
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set("sensor.export", "100", {"unit_of_measurement": "W"})
    await setup(hass, config_entry)
    await tick(hass, freezer, 60)
    coordinator = config_entry.runtime_data.coordinator
    coordinator.async_set_updated_data({**coordinator.data, "api_data": sample_api_response()})
    await hass.async_block_till_done()
    await tick(hass, freezer, 61)
    coordinator.async_set_updated_data(
        {**coordinator.data, "api_data": sample_api_response(bridage=1)}
    )
    await hass.async_block_till_done()
    state_id = entity_id(hass, config_entry, "binary_sensor", "injection_during_limitation")
    assert hass.states.get(state_id).state == "off"
    await tick(hass, freezer, 121)
    assert hass.states.get(state_id).state == "on"


async def test_reload_does_not_command_relays_during_bypass(hass, config_entry, mock_fetch):
    mock_fetch.return_value = sample_api_response(bridage=1)
    hass.states.async_set(RELAY_ENTITY, "on")
    calls = await setup(hass, config_entry)
    bypass_id = entity_id(hass, config_entry, "switch", "manual_bypass")
    await hass.data["switch"].get_entity(bypass_id).async_turn_on()
    await hass.async_block_till_done()
    hass.states.async_set(RELAY_ENTITY, "off")
    await hass.async_block_till_done()
    calls.clear()
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_id).state == "on"
    assert calls == []


async def test_api_recovery_starts_control_without_reload(hass, config_entry, mock_fetch, freezer):
    mock_fetch.side_effect = ThreeERLApiError("offline")
    hass.states.async_set(RELAY_ENTITY, "off")
    calls = await setup(hass, config_entry)
    assert calls == []
    mock_fetch.side_effect = None
    mock_fetch.return_value = sample_api_response(bridage=1)
    await tick(hass, freezer, 61)
    assert config_entry.runtime_data.coordinator.last_update_success
    assert len(calls) == 1


async def test_options_save_during_api_outage(hass, config_entry, mock_fetch):
    mock_fetch.side_effect = ThreeERLApiError("offline")
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            **config_entry.data,
            "pv_power_entity": ["sensor.pv_power"],
            "relay_entity": [RELAY_ENTITY],
            "injection_power_entity": "sensor.export",
            "injection_threshold": 75,
            "injection_delay": 90,
            "injection_max_age": 180,
        },
    )
    assert result["type"] == "create_entry"
    assert config_entry.options["injection_power_entity"] == "sensor.export"
    assert config_entry.options["injection_threshold"] == 75
    assert mock_fetch.call_count == 0


async def test_new_entity_identifiers(hass, config_entry, mock_fetch):
    await setup(hass, config_entry)
    for domain, key, suffix in (
        ("sensor", "energie_bridage_kwh", "curtailed_energy"),
        ("binary_sensor", "commanded_limitation", "commanded_limitation"),
    ):
        expected_id = f"{domain}.3erl_zero_injection_{suffix}"
        assert entity_id(hass, config_entry, domain, key) == expected_id
        assert hass.states.get(expected_id) is not None
    registry = er.async_get(hass)
    for domain, key in (
        ("sensor", "gain_cumule_eur"),
        ("sensor", "puissance_gain"),
        ("sensor", "estimated_cumulative_remuneration"),
        ("sensor", "estimated_hourly_remuneration"),
        ("binary_sensor", "zero_inject_active"),
    ):
        assert (
            registry.async_get_entity_id(domain, DOMAIN, f"{DOMAIN}_{config_entry.entry_id}_{key}")
            is None
        )
