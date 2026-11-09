"""Diagnostics support for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import ThreeERLConfigEntry
from .helpers import entry_settings, relay_entities


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ThreeERLConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry to diagnose.
    :type entry: ThreeERLConfigEntry
    :return: Serializable diagnostic data.
    :rtype: dict[str, Any]
    """
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    pricing = runtime.pricing_coordinator
    return {
        "settings": dict(entry_settings(entry)),
        "signal": {
            "last_update_success": coordinator.last_update_success,
            "curtailment_requested": coordinator.curtailment_requested,
            "data_age_minutes": coordinator.data_age_minutes,
            "data_stale": coordinator.data_stale,
            "update_interval_seconds": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
        },
        "pricing": {
            "last_update_success": pricing.last_update_success,
            "data": pricing.data,
        },
        "control": {
            "commanded_limitation": runtime.controller.commanded_active,
            "manual_bypass": runtime.controller.bypassed,
            "relay_states": {
                entity_id: state.state if (state := hass.states.get(entity_id)) else None
                for entity_id in relay_entities(entry_settings(entry))
            },
        },
    }
