"""Pricing data manager for improved 3ERL remuneration estimation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.util.dt import now as dt_now

from .const import (
    API_TIMEOUT_SECONDS,
    DEFAULT_ENEDIS_PRD3_API_URL,
    DEFAULT_PRD3_DAY_OFFSET,
    DEFAULT_PRD3_PROFILE,
    DEFAULT_RTE_PRICE_API_URL,
)

_LOGGER = logging.getLogger(__name__)

SLOTS_PER_DAY = 96
MINUTES_PER_SLOT = 15


class PricingDataError(Exception):
    """Error fetching or parsing pricing data."""


class PricingDataManager:
    """Fetches RTE PRE+ and Enedis PRD3 data and computes price estimates.

    The manager fetches two public datasets:

    - RTE equilibrage API: quarter-hourly PRE+ values for the current day.
    - Enedis open data API: PRD3 dynamic profile coefficients for a past day,
      used to estimate the daily weighted average PRE+ for ACI contracts.

    :param session: Shared aiohttp client session.
    :type session: aiohttp.ClientSession
    :param prd3_day_offset: Day offset used to select the PRD3 profile.
        Default is -2 because Enedis publishes yesterday's profile late in the
        morning of the following day.
    :type prd3_day_offset: int
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        prd3_day_offset: int = DEFAULT_PRD3_DAY_OFFSET,
    ) -> None:
        """Initialize the pricing data manager."""
        self._session = session
        self._prd3_day_offset = prd3_day_offset
        self._rte_url = DEFAULT_RTE_PRICE_API_URL
        self._enedis_url = DEFAULT_ENEDIS_PRD3_API_URL

        self._prep_values: dict[datetime, float] = {}
        self._prd3_values: dict[datetime, float] = {}
        self._estimated_daily_prep: float | None = None

    @property
    def estimated_daily_prep(self) -> float | None:
        """Return the current estimated daily PRE+ for ACI contracts.

        :return: Estimated daily PRE+ in EUR/MWh, or None if not computable.
        :rtype: float | None
        """
        return self._estimated_daily_prep

    def current_prep(self) -> float | None:
        """Return the PRE+ for the current quarter-hour slot.

        This is the value used for ACC contracts.

        :return: Current quarter-hour PRE+ in EUR/MWh, or None if unavailable.
        :rtype: float | None
        """
        slot = self._current_slot()
        return self._prep_values.get(slot)

    async def async_update(self) -> None:
        """Fetch RTE and Enedis data and refresh the price estimates."""
        self._prep_values = await self._fetch_rte_prep()
        self._prd3_values = await self._fetch_prd3_profile()
        self._estimated_daily_prep = self._compute_estimated_daily_prep()

        _LOGGER.debug(
            "Pricing data updated: %d PREP slots, %d PRD3 slots, estimated_daily_prep=%s",
            len(self._prep_values),
            len(self._prd3_values),
            self._estimated_daily_prep,
        )

    def _current_slot(self) -> datetime:
        """Return the start of the current quarter-hour slot in Europe/Paris.

        :return: Quarter-hour slot start as a timezone-aware datetime.
        :rtype: datetime
        """
        current = dt_now()
        minute = (current.minute // MINUTES_PER_SLOT) * MINUTES_PER_SLOT
        return current.replace(minute=minute, second=0, microsecond=0)

    async def _fetch_rte_prep(self) -> dict[datetime, float]:
        """Fetch quarter-hourly PRE+ values from RTE.

        :return: Mapping from slot start datetime to PRE+ value.
        :rtype: dict[datetime, float]
        :raises PricingDataError: If the request or parsing fails.
        """
        day = dt_now().date()
        params = {"startDate": day.strftime("%d/%m/%Y")}

        try:
            async with self._session.get(
                self._rte_url, params=params, timeout=API_TIMEOUT_SECONDS
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as err:
            raise PricingDataError(f"Failed to fetch RTE pricing data: {err}") from err
        except Exception as err:
            raise PricingDataError(f"Unexpected error fetching RTE data: {err}") from err

        values = data.get("values", []) if isinstance(data, dict) else []
        result: dict[datetime, float] = {}
        for item in values:
            if not isinstance(item, dict):
                continue
            slot = self._parse_datetime(item.get("date"))
            pre = item.get("pre")
            if slot is None or not isinstance(pre, dict):
                continue
            positive = pre.get("positive")
            if positive is None:
                continue
            try:
                result[slot] = float(positive)
            except (ValueError, TypeError):
                continue
        return result

    async def _fetch_prd3_profile(self) -> dict[datetime, float]:
        """Fetch the PRD3 profile coefficients from Enedis for the selected day.

        :return: Mapping from slot start datetime to PRD3 coefficient.
        :rtype: dict[datetime, float]
        :raises PricingDataError: If the request or parsing fails.
        """
        target_day = dt_now().date() + timedelta(days=self._prd3_day_offset)
        start = datetime.combine(target_day, datetime.min.time())
        end = start + timedelta(days=1, minutes=-MINUTES_PER_SLOT)

        payload = {
            "action": "exports",
            "output": "exportDirect",
            "format": "json",
            "dataset": "koumoul://7okolrt07nor9cv103spkfzc",
            "apikey": "false",
            "datefield": "horodate",
            "select": "horodate, coefficient_dynamique_j_1",
            "where": (
                f"(sous_profil='{DEFAULT_PRD3_PROFILE}') "
                f"AND horodate >= '{start.isoformat()}' "
                f"AND horodate <= '{end.isoformat()}'"
            ),
            "group": "",
            "order": "horodate desc",
        }

        try:
            async with self._session.post(
                self._enedis_url, data=payload, timeout=API_TIMEOUT_SECONDS
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientError as err:
            raise PricingDataError(f"Failed to fetch Enedis PRD3 data: {err}") from err
        except Exception as err:
            raise PricingDataError(f"Unexpected error fetching PRD3 data: {err}") from err

        if not isinstance(data, list):
            raise PricingDataError("Unexpected Enedis PRD3 response format")

        result: dict[datetime, float] = {}
        for item in data:
            if not isinstance(item, dict):
                continue
            slot = self._parse_datetime(item.get("horodate"))
            coefficient = item.get("coefficient_dynamique_j_1")
            if slot is None or coefficient is None:
                continue
            try:
                result[slot] = float(coefficient)
            except (ValueError, TypeError):
                continue
        return result

    def _compute_estimated_daily_prep(self) -> float | None:
        """Compute the daily weighted average PRE+ using the PRD3 profile.

        The PREP values are for the current day, while the PRD3 profile is taken
        from a past day. The two datasets are aligned by time-of-day (hour and
        minute), not by the full date, because Enedis applies the same sunlight
        shape regardless of the calendar day.

        Formula: sum(PREP * PRD3) / sum(PRD3)

        :return: Estimated daily PRE+ in EUR/MWh, or None if not computable.
        :rtype: float | None
        """
        if not self._prep_values or not self._prd3_values:
            return None

        prd3_by_time: dict[tuple[int, int], float] = {
            (slot.hour, slot.minute): factor for slot, factor in self._prd3_values.items()
        }

        weighted_sum = 0.0
        factor_sum = 0.0
        for slot, prep in self._prep_values.items():
            factor = prd3_by_time.get((slot.hour, slot.minute))
            if factor is None or factor <= 0:
                continue
            weighted_sum += prep * factor
            factor_sum += factor

        if factor_sum <= 0:
            return None
        return weighted_sum / factor_sum

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse an ISO datetime string into a timezone-aware datetime.

        :param value: Datetime string or None.
        :type value: Any
        :return: Parsed datetime, or None if not parseable.
        :rtype: datetime | None
        """
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
