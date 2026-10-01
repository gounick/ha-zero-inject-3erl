"""Tests for shared zero-injection helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.zero_inject_3erl.helpers import (
    compute_zero_inject_active,
    curtailment_signal_key,
    get_current_mode,
    is_bridage_active,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, True),
        ("1", False),
        ("true", True),
        ("True", True),
        ("on", True),
        ("yes", True),
        (0, False),
        ("false", False),
        (None, False),
    ],
)
def test_is_bridage_active(value: object, expected: bool) -> None:
    """Test the curtailment flag parser."""
    assert is_bridage_active({"Bridage": value}) == expected


@pytest.mark.parametrize(
    ("aggregation_mode", "api_data", "expected"),
    [
        ("aci", {"Bridage": 1, "Bridage_CDC": 0}, True),
        ("aci", {"Bridage": 0, "Bridage_CDC": 1}, False),
        ("acc", {"Bridage": 0, "Bridage_CDC": 1}, True),
        ("acc", {"Bridage": 1, "Bridage_CDC": 0}, False),
        ("unknown_mode", {"Bridage": 1}, True),
    ],
)
def test_is_bridage_active_aggregation_mode(
    aggregation_mode: str, api_data: dict, expected: bool
) -> None:
    """Test that the aggregation mode selects the right API signal."""
    assert is_bridage_active(api_data, aggregation_mode) == expected


def test_curtailment_signal_key() -> None:
    """Test the signal key mapping per contract type."""
    assert curtailment_signal_key("aci") == "Bridage"
    assert curtailment_signal_key("acc") == "Bridage_CDC"
    assert curtailment_signal_key() == "Bridage"


def test_get_current_mode_default() -> None:
    """Test that a missing mode entity returns Auto."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.states.get.return_value = None
    assert get_current_mode(hass, None) == "Auto"


def test_get_current_mode_from_state() -> None:
    """Test reading the mode from the select entity state."""
    hass = MagicMock()
    state = MagicMock()
    state.state = "On"
    hass.states.get.return_value = state
    assert get_current_mode(hass, "select.zero_inject_3erl_mode") == "On"


def test_get_current_mode_invalid_state() -> None:
    """Test that an invalid mode state falls back to Auto."""
    hass = MagicMock()
    state = MagicMock()
    state.state = "Invalid"
    hass.states.get.return_value = state
    assert get_current_mode(hass, "select.zero_inject_3erl_mode") == "Auto"


@pytest.mark.parametrize(
    ("mode", "bridage_active", "expected"),
    [
        ("On", False, True),
        ("Off", True, False),
        ("Auto", True, True),
        ("Auto", False, False),
    ],
)
def test_compute_zero_inject_active(mode: str, bridage_active: bool, expected: bool) -> None:
    """Test the active-state decision helper."""
    assert compute_zero_inject_active(mode, bridage_active) == expected
