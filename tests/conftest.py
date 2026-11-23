"""Shared fixtures for the 3ERL Zero-Injection tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.const import (
    API_TIME_FORMAT,
    API_TIMEZONE,
    CONF_AGGREGATION_MODE,
    CONF_API_URL,
    CONF_RELAY_ENTITY,
    DEFAULT_API_URL,
    DOMAIN,
)

RELAY_ENTITY = "switch.relay"


def sample_api_response(bridage: int = 0, heure_update: str = "30/09/2026 15:00") -> dict[str, Any]:
    """Return a sample 3ERL API response.

    :param bridage: Value of the ACI curtailment flag.
    :type bridage: int
    :param heure_update: Value of the ``Heure_Update`` publication time.
    :type heure_update: str
    :return: Sample API payload.
    :rtype: dict[str, Any]
    """
    return {
        "Bridage": bridage,
        "Bridage_CDC": 0,
        "Dernier_PREP": 150.0,
        "Heure_Update": heure_update,
        "PREP_Profile": "1+",
        "PRD4": 120.0,
        "Bridage_Long_Terme": 0,
    }


def fresh_heure_update() -> str:
    """Return a ``Heure_Update`` value timestamped at the current time."""
    return dt_util.now(API_TIMEZONE).strftime(API_TIME_FORMAT)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the custom integration in every test."""


@pytest.fixture(autouse=True)
async def setup_switch_domain(hass: HomeAssistant) -> None:
    await async_setup_component(hass, "switch", {})


@pytest.fixture
def mock_fetch() -> Generator[AsyncMock]:
    """Patch the 3ERL API client and the external pricing sources."""
    with (
        patch(
            "custom_components.zero_inject_3erl.api.ThreeERLApiClient.fetch",
            return_value=sample_api_response(),
        ) as fetch,
        patch(
            "custom_components.zero_inject_3erl.pricing.PricingDataManager.async_update",
            return_value=None,
        ),
    ):
        yield fetch


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry added to Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={
            CONF_API_URL: DEFAULT_API_URL,
            CONF_AGGREGATION_MODE: "aci",
            CONF_RELAY_ENTITY: RELAY_ENTITY,
        },
    )
    entry.add_to_hass(hass)
    return entry
