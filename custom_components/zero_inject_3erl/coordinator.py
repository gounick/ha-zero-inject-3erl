"""DataUpdateCoordinator for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import (
    AGGREGATION_MODE_ACC,
    API_FALLBACK_INTERVAL,
    API_RETRY_INTERVAL,
    API_TIMEZONE,
    CONF_AGGREGATION_MODE,
    CONF_CONSUMPTION_POWER_ENTITY,
    CONF_PRD3_DAY_OFFSET,
    CONF_PV_POWER_ENTITY,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_PRD3_DAY_OFFSET,
    DOMAIN,
    MEGAWATT_HOURS_PER_KILOWATT_HOUR,
    POWER_UPDATE_INTERVAL,
    REMUNERATION_RATE,
    SECONDS_PER_HOUR,
    SENSOR_KEY_DERNIER_PREP,
    SENSOR_KEY_HEURE_UPDATE,
    STORAGE_KEY,
    STORE_SAVE_DELAY_SECONDS,
    WATTS_PER_KILOWATT,
)
from .helpers import entry_settings, is_bridage_active, next_poll_delay
from .pricing import PricingDataError, PricingDataManager

_LOGGER = logging.getLogger(__name__)


class ThreeERLUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the 3ERL API and tracks curtailed energy.

    The coordinator polls the public 3ERL API when new data is expected (see
    ``helpers.next_poll_delay``) and also reacts to changes of the configured
    PV production power sensor. When curtailment is active it accumulates the
    energy that would have been injected and the estimated 3ERL remuneration.

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
        session: aiohttp.ClientSession,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        settings = entry_settings(entry)
        self._api_client = api_client
        self._entry = entry
        self._pv_power_entity = settings[CONF_PV_POWER_ENTITY]
        self._consumption_entity = settings.get(CONF_CONSUMPTION_POWER_ENTITY)
        self._aggregation_mode = settings.get(CONF_AGGREGATION_MODE, DEFAULT_AGGREGATION_MODE)
        prd3_offset = settings.get(CONF_PRD3_DAY_OFFSET, DEFAULT_PRD3_DAY_OFFSET)
        self._pricing = PricingDataManager(session, prd3_offset)
        self._cumulative_energy_kwh = 0.0
        self._cumulative_gain_eur = 0.0
        self._last_update_time: datetime | None = None
        self._store = Store(hass, 1, f"{STORAGE_KEY}_{entry.entry_id}")

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=API_FALLBACK_INTERVAL,
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

    @property
    def curtailment_requested(self) -> bool:
        """Return whether the latest API data requests curtailment.

        :return: True when the signal of the configured contract type is set.
        :rtype: bool
        """
        api_data = self.data.get("api_data", {}) if self.data else {}
        return is_bridage_active(api_data, self._aggregation_mode)

    async def async_shutdown(self) -> None:
        """Stop tracking the PV power sensor, flush counters and shut down."""
        self._unsub_power()
        await self._store_cumulative_data()
        await super().async_shutdown()

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
            self.update_interval = API_RETRY_INTERVAL
            raise UpdateFailed(f"Failed to fetch 3ERL data: {err}") from err
        self.update_interval = next_poll_delay(
            api_data.get(SENSOR_KEY_HEURE_UPDATE), dt_util.now(API_TIMEZONE)
        )

        try:
            await self._pricing.async_update()
        except PricingDataError as err:
            _LOGGER.warning("Pricing data refresh failed: %s", err)

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
        self._async_push_computed_data()

    @callback
    def _async_push_computed_data(self) -> None:
        """Recompute derived values and notify listeners.

        Unlike ``async_set_updated_data``, this keeps the scheduled API poll.
        Frequent PV power changes would otherwise postpone it forever.
        """
        api_data = self.data.get("api_data", {}) if self.data else {}
        self.data = self._build_data(api_data)
        self.async_update_listeners()

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

        power_w = self._curtailable_power()
        if power_w is None:
            self._last_update_time = now
            return

        if api_data is None:
            api_data = self.data.get("api_data", {}) if self.data else {}
        bridage_active = is_bridage_active(api_data, self._aggregation_mode)
        current_price = self._current_price(api_data)

        if bridage_active and power_w > 0:
            energy_delta_kwh = (power_w * delta_hours) / WATTS_PER_KILOWATT
            self._cumulative_energy_kwh += energy_delta_kwh

            if current_price is not None and current_price > 0:
                gain_delta_eur = (
                    energy_delta_kwh
                    * current_price
                    * REMUNERATION_RATE
                    / MEGAWATT_HOURS_PER_KILOWATT_HOUR
                )
                self._cumulative_gain_eur += gain_delta_eur

            self._store.async_delay_save(self._cumulative_data, STORE_SAVE_DELAY_SECONDS)

        self._last_update_time = now

    def _curtailable_power(self) -> float | None:
        """Return the power lost to curtailment, in watts.

        Without a consumption sensor this is the raw PV production, an upper
        bound of the surplus that would have been injected. With one, it is
        production minus home consumption, clipped at zero. If the configured
        consumption sensor is unreadable, production is used as a fallback.

        :return: Curtailable power in watts, or None if the PV sensor is down.
        :rtype: float | None
        """
        power_w = self._numeric_state(self.hass.states.get(self._pv_power_entity))
        if power_w is None:
            return None
        if not self._consumption_entity:
            return power_w
        consumption_w = self._numeric_state(self.hass.states.get(self._consumption_entity))
        if consumption_w is None:
            return power_w
        return max(power_w - consumption_w, 0.0)

    def _current_price(self, api_data: dict[str, Any]) -> float | None:
        """Return the price to use for the current remuneration estimate.

        For ACC this is the current quarter-hour PRE+. For ACI it is the
        estimated daily PRE+ computed from the PRD3 profile. If the external
        pricing sources are unavailable, fall back to the latest 3ERL PRE+.

        :param api_data: Raw data returned by the 3ERL API.
        :type api_data: dict[str, Any]
        :return: Price in EUR/MWh, or None if unavailable.
        :rtype: float | None
        """
        if self._aggregation_mode == AGGREGATION_MODE_ACC:
            return self._pricing.current_prep() or self._numeric_value(
                api_data.get(SENSOR_KEY_DERNIER_PREP)
            )
        estimated = self._pricing.estimated_daily_prep
        if estimated is not None:
            return estimated
        return self._numeric_value(api_data.get(SENSOR_KEY_DERNIER_PREP))

    def _build_data(self, api_data: dict[str, Any]) -> dict[str, Any]:
        """Combine API data with computed power, energy and gain values.

        :param api_data: Raw data returned by the 3ERL API.
        :type api_data: dict[str, Any]
        :return: Combined data used by sensor entities.
        :rtype: dict[str, Any]
        """
        pv_power_w = self._numeric_state(self.hass.states.get(self._pv_power_entity)) or 0.0
        power_w = self._curtailable_power() or 0.0
        bridage_active = is_bridage_active(api_data, self._aggregation_mode)
        current_price = self._current_price(api_data) or 0.0

        puissance_bridable = power_w if bridage_active else 0.0
        gain_per_mwh = REMUNERATION_RATE / MEGAWATT_HOURS_PER_KILOWATT_HOUR
        puissance_gain = puissance_bridable * current_price * gain_per_mwh / WATTS_PER_KILOWATT

        return {
            "api_data": api_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "aggregation_mode": self._aggregation_mode,
            "pv_power_w": pv_power_w,
            "current_prep": self._pricing.current_prep(),
            "estimated_daily_prep": self._pricing.estimated_daily_prep,
            "puissance_bridable": puissance_bridable,
            "puissance_gain": round(puissance_gain, 6),
            "energie_bridage_kwh": round(self._cumulative_energy_kwh, 4),
            "gain_cumule_eur": round(self._cumulative_gain_eur, 4),
        }

    @callback
    def _cumulative_data(self) -> dict[str, float]:
        """Return the cumulative values to persist.

        :return: Cumulative energy and gain.
        :rtype: dict[str, float]
        """
        return {
            "energy_kwh": self._cumulative_energy_kwh,
            "gain_eur": self._cumulative_gain_eur,
        }

    async def _store_cumulative_data(self) -> None:
        """Persist cumulative energy and gain values now."""
        await self._store.async_save(self._cumulative_data())

    async def async_reset_counters(self) -> None:
        """Reset cumulative energy and gain values to zero."""
        self._cumulative_energy_kwh = 0.0
        self._cumulative_gain_eur = 0.0
        await self._store_cumulative_data()
        self._async_push_computed_data()
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
