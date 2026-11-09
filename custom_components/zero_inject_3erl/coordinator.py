"""DataUpdateCoordinator for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import (
    API_FALLBACK_INTERVAL,
    API_RETRY_INTERVAL,
    API_STALE_AFTER,
    CONF_AGGREGATION_MODE,
    CONF_PRD3_DAY_OFFSET,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_PRD3_DAY_OFFSET,
    DOMAIN,
    SENSOR_KEY_HEURE_UPDATE,
)
from .helpers import entry_settings, is_bridage_active, next_poll_delay, parse_heure_update
from .pricing import PricingDataError, PricingDataManager

_LOGGER = logging.getLogger(__name__)


class ThreeERLUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the 3ERL control signal independently of informational prices."""

    def __init__(
        self, hass: HomeAssistant, api_client: ThreeERLApiClient, entry: ConfigEntry
    ) -> None:
        """Initialize the signal coordinator."""
        self._api_client = api_client
        self._aggregation_mode = entry_settings(entry).get(
            CONF_AGGREGATION_MODE, DEFAULT_AGGREGATION_MODE
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=API_FALLBACK_INTERVAL,
        )

    @property
    def aggregation_mode(self) -> str:
        """Return the configured contract type."""
        return self._aggregation_mode

    @property
    def curtailment_requested(self) -> bool | None:
        """Return the last valid demand, or None before receiving a signal."""
        api_data = self.data.get("api_data", {}) if self.data else {}
        return is_bridage_active(api_data, self._aggregation_mode)

    @property
    def data_age_minutes(self) -> float | None:
        """Return the live age of the last publication in minutes."""
        api_data = (self.data or {}).get("api_data", {})
        published = parse_heure_update(api_data.get(SENSOR_KEY_HEURE_UPDATE))
        if published is None:
            return None
        return round((dt_util.utcnow() - published.astimezone(UTC)).total_seconds() / 60, 1)

    @property
    def data_stale(self) -> bool | None:
        """Return whether the last publication is expired or in the future."""
        age = self.data_age_minutes
        if age is None:
            return None
        return age < 0 or age > API_STALE_AFTER.total_seconds() / 60

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch only the control signal, preserving valid data on failure."""
        try:
            api_data = await self._api_client.fetch()
        except ThreeERLApiError as err:
            self.update_interval = API_RETRY_INTERVAL
            raise UpdateFailed(f"Failed to fetch 3ERL data: {err}") from err
        self.update_interval = next_poll_delay(
            api_data.get(SENSOR_KEY_HEURE_UPDATE), dt_util.utcnow()
        )
        return {
            "api_data": api_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "aggregation_mode": self._aggregation_mode,
        }


class ThreeERLPricingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Refresh informational prices without blocking relay control."""

    def __init__(
        self, hass: HomeAssistant, session: aiohttp.ClientSession, entry: ConfigEntry
    ) -> None:
        """Initialize the independent pricing coordinator."""
        offset = entry_settings(entry).get(CONF_PRD3_DAY_OFFSET, DEFAULT_PRD3_DAY_OFFSET)
        self._pricing = PricingDataManager(session, offset)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_pricing",
            update_interval=API_FALLBACK_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh prices on their own schedule."""
        try:
            await self._pricing.async_update()
        except PricingDataError as err:
            raise UpdateFailed(f"Failed to fetch pricing data: {err}") from err
        return {
            "current_prep": self._pricing.current_prep(),
            "estimated_daily_prep": self._pricing.estimated_daily_prep,
            "estimated_daily_prep_coverage": self._pricing.estimated_daily_prep_coverage,
        }
