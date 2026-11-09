"""Tests for the 3ERL data coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zero_inject_3erl.api import ThreeERLApiError
from custom_components.zero_inject_3erl.const import DOMAIN
from custom_components.zero_inject_3erl.coordinator import ThreeERLUpdateCoordinator

from .conftest import sample_api_response


@pytest.fixture
def coordinator(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    api = AsyncMock()
    api.fetch.return_value = sample_api_response(bridage=1)
    return ThreeERLUpdateCoordinator(hass, api, entry)


async def test_failed_refresh_preserves_last_signal(coordinator):
    await coordinator.async_refresh()
    coordinator._api_client.fetch.side_effect = ThreeERLApiError("offline")
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.curtailment_requested is True
    assert coordinator.update_interval == timedelta(minutes=1)


async def test_age_increases_without_power_or_api_updates(coordinator, freezer):
    now = dt_util.now().astimezone(__import__("zoneinfo").ZoneInfo("Europe/Paris"))
    coordinator._api_client.fetch.return_value = {
        **sample_api_response(),
        "Heure_Update": (now - timedelta(minutes=10)).strftime("%d/%m/%Y %H:%M"),
    }
    await coordinator.async_refresh()
    assert coordinator.data_stale is False
    freezer.tick(timedelta(minutes=21))
    assert coordinator.data_stale is True
    assert coordinator.data_age_minutes >= 31


def test_no_signal_is_unknown(coordinator):
    assert coordinator.curtailment_requested is None
    assert coordinator.data_stale is None


async def test_future_publication_is_not_fresh(coordinator):
    coordinator._api_client.fetch.return_value = {
        **sample_api_response(),
        "Heure_Update": "01/01/2099 12:00",
    }
    await coordinator.async_refresh()
    assert coordinator.data_stale is True
    assert coordinator.update_interval == timedelta(minutes=1)
