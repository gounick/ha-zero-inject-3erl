"""Tests for shared zero-injection helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.zero_inject_3erl.helpers import (
    compute_zero_inject_active,
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
