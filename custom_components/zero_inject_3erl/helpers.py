"""Shared helpers for zero-injection logic."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import DEFAULT_ZERO_INJECT_MODE, SENSOR_KEY_BRIDAGE, ZERO_INJECT_MODES


def is_bridage_active(api_data: dict[str, Any]) -> bool:
    """Return whether the 3ERL API requests curtailment.

    :param api_data: Raw data returned by the 3ERL API.
    :type api_data: dict[str, Any]
    :return: True when curtailment is requested.
    :rtype: bool
    """
    bridage = api_data.get(SENSOR_KEY_BRIDAGE)
    return bridage == 1 or str(bridage).lower() in ("true", "on", "yes")


def get_current_mode(hass: HomeAssistant, mode_entity_id: str | None) -> str:
    """Return the current zero-injection mode from the select entity.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param mode_entity_id: Entity id of the mode select, or None.
    :type mode_entity_id: str | None
    :return: One of Auto, On, Off.
    :rtype: str
    """
    if mode_entity_id is None:
        return DEFAULT_ZERO_INJECT_MODE
    state = hass.states.get(mode_entity_id)
    if state is None or state.state not in ZERO_INJECT_MODES:
        return DEFAULT_ZERO_INJECT_MODE
    return state.state


def compute_zero_inject_active(mode: str, bridage_active: bool) -> bool:
    """Return whether zero-injection should be active.

    :param mode: Current zero-injection mode.
    :type mode: str
    :param bridage_active: Whether curtailment is requested by the API.
    :type bridage_active: bool
    :return: True when the relay should be turned on.
    :rtype: bool
    """
    if mode == "On":
        return True
    if mode == "Off":
        return False
    return bridage_active
