"""DataUpdateCoordinator for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import (
    CONF_AGGREGATION_MODE,
    CONF_PV_POWER_ENTITY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MEGAWATT_HOURS_PER_KILOWATT_HOUR,
    POWER_UPDATE_INTERVAL,
    REMUNERATION_RATE,
    SECONDS_PER_HOUR,
    SENSOR_KEY_DERNIER_PREP,
    STORAGE_KEY,
    WATTS_PER_KILOWATT,
)
from .helpers import is_bridage_active

_LOGGER = logging.getLogger(__name__)


class ThreeERLUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the 3ERL API and tracks curtailed energy.

    The coordinator polls the public 3ERL API on a configurable interval and
    also reacts to changes of the configured PV production power sensor. When
    curtailment is active it accumulates the energy that would have been
    injected and the estimated 3ERL remuneration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param api_client: Initialized 3ERL API client.
    :type api_client: ThreeERLApiClient
    :param entry: Config entry for this instance.
    :type entry: ConfigEntry
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: ThreeERLApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self._api_client = api_client
        self._entry = entry
        self._pv_power_entity = entry.options.get(
            CONF_PV_POWER_ENTITY, entry.data[CONF_PV_POWER_ENTITY]
        )
        self._aggregation_mode = entry.options.get(
            CONF_AGGREGATION_MODE,
            entry.data.get(CONF_AGGREGATION_MODE, DEFAULT_AGGREGATION_MODE),
        )
        self._cumulative_energy_kwh = 0.0
        self._cumulative_gain_eur = 0.0
        self._last_update_time: datetime | None = None
        self._store = Store(hass, 1, f"{STORAGE_KEY}_{entry.entry_id}")

        update_minutes = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MINUTES),
        )
        update_interval = timedelta(minutes=update_minutes)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        self._unsub_power = async_track_state_change_event(
            hass,
            [self._pv_power_entity],
            self._handle_power_state_change,
        )

    @property
    def aggregation_mode(self) -> str:
        """Return the configured self-consumption contract type.

        :return: "aci" or "acc".
        :rtype: str
        """
        return self._aggregation_mode

    async def async_load_cumulative_data(self) -> None:
        """Restore cumulative energy and gain values from storage."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self._cumulative_energy_kwh = float(data.get("energy_kwh", 0.0))
            self._cumulative_gain_eur = float(data.get("gain_eur", 0.0))
            _LOGGER.debug(
                "Restored cumulative data: %.4f kWh, %.4f EUR",
                self._cumulative_energy_kwh,
                self._cumulative_gain_eur,
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the 3ERL API.

        :return: Combined API and computed data.
        :rtype: dict[str, Any]
        :raises UpdateFailed: If the API request fails.
        """
        try:
            api_data = await self._api_client.fetch()
        except ThreeERLApiError as err:
            raise UpdateFailed(f"Failed to fetch 3ERL data: {err}") from err

        self._accumulate_from_power_sensor()

        return self._build_data(api_data)

    @callback
    def _handle_power_state_change(self, event: Any) -> None:
        """React to a state change of the PV production power sensor."""
        now = datetime.now(UTC)
        if self._last_update_time is not None:
            delta = now - self._last_update_time
            if delta < POWER_UPDATE_INTERVAL:
                return
        self._accumulate_from_power_sensor(now)
        api_data = self.data.get("api_data", {}) if self.data else {}
        self.async_set_updated_data(self._build_data(api_data))

    def _accumulate_from_power_sensor(
        self,
        now: datetime | None = None,
        api_data: dict[str, Any] | None = None,
    ) -> None:
        """Accumulate curtailed energy and gain from the PV power sensor.

        :param now: Optional timestamp for the update. Defaults to UTC now.
        :type now: datetime | None
        :param api_data: Optional API data to use instead of coordinator data.
        :type api_data: dict[str, Any] | None
        """
        if now is None:
            now = datetime.now(UTC)

        if self._last_update_time is None:
            self._last_update_time = now
            return

        delta_hours = (now - self._last_update_time).total_seconds() / SECONDS_PER_HOUR
        if delta_hours <= 0:
            return

        power_state = self.hass.states.get(self._pv_power_entity)
        power_w = self._numeric_state(power_state)
        if power_w is None:
            self._last_update_time = now
            return

        if api_data is None:
            api_data = self.data.get("api_data", {}) if self.data else {}
        bridage_active = is_bridage_active(api_data, self._aggregation_mode)
        dernier_prep = self._numeric_value(api_data.get(SENSOR_KEY_DERNIER_PREP))

        if bridage_active and power_w > 0:
            energy_delta_kwh = (power_w * delta_hours) / WATTS_PER_KILOWATT
            self._cumulative_energy_kwh += energy_delta_kwh

            if dernier_prep is not None and dernier_prep > 0:
                gain_delta_eur = (
                    energy_delta_kwh
                    * dernier_prep
                    * REMUNERATION_RATE
                    / MEGAWATT_HOURS_PER_KILOWATT_HOUR
                )
                self._cumulative_gain_eur += gain_delta_eur

            self.hass.async_create_background_task(
                self._store_cumulative_data(), name=f"{DOMAIN}_store_cumulative"
            )

        self._last_update_time = now

    def _build_data(self, api_data: dict[str, Any]) -> dict[str, Any]:
        """Combine API data with computed power, energy and gain values.

        :param api_data: Raw data returned by the 3ERL API.
        :type api_data: dict[str, Any]
        :return: Combined data used by sensor entities.
        :rtype: dict[str, Any]
        """
        power_state = self.hass.states.get(self._pv_power_entity)
        power_w = self._numeric_state(power_state) or 0.0
        bridage_active = is_bridage_active(api_data, self._aggregation_mode)
        dernier_prep = self._numeric_value(api_data.get(SENSOR_KEY_DERNIER_PREP)) or 0.0

        puissance_bridable = power_w if bridage_active else 0.0
        gain_per_mwh = REMUNERATION_RATE / MEGAWATT_HOURS_PER_KILOWATT_HOUR
        puissance_gain = puissance_bridable * dernier_prep * gain_per_mwh / WATTS_PER_KILOWATT

        return {
            "api_data": api_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "aggregation_mode": self._aggregation_mode,
            "pv_power_w": power_w,
            "puissance_bridable": puissance_bridable,
            "puissance_gain": round(puissance_gain, 6),
            "energie_bridage_kwh": round(self._cumulative_energy_kwh, 4),
            "gain_cumule_eur": round(self._cumulative_gain_eur, 4),
        }

    async def _store_cumulative_data(self) -> None:
        """Persist cumulative energy and gain values."""
        await self._store.async_save(
            {
                "energy_kwh": self._cumulative_energy_kwh,
                "gain_eur": self._cumulative_gain_eur,
            }
        )

    async def async_reset_counters(self) -> None:
        """Reset cumulative energy and gain values to zero."""
        self._cumulative_energy_kwh = 0.0
        self._cumulative_gain_eur = 0.0
        await self._store_cumulative_data()
        api_data = self.data.get("api_data", {}) if self.data else {}
        self.async_set_updated_data(self._build_data(api_data))
        _LOGGER.info("Reset 3ERL cumulative energy and gain counters")

    @staticmethod
    def _numeric_state(state_obj: Any) -> float | None:
        """Extract a float value from a HA state object.

        :param state_obj: HA State object or None.
        :type state_obj: Any
        :return: Parsed float value, or None if unavailable.
        :rtype: float | None
        """
        if state_obj is None or state_obj.state in (None, "unavailable", "unknown"):
            return None
        try:
            return float(state_obj.state)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _numeric_value(value: Any) -> float | None:
        """Parse a value as float.

        :param value: Value to parse.
        :type value: Any
        :return: Parsed float value, or None if not parseable.
        :rtype: float | None
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
