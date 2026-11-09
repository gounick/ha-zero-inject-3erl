"""Client for the 3ERL public API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.util import dt as dt_util

from .const import API_TIMEOUT_SECONDS, DEFAULT_AGGREGATION_MODE, SENSOR_KEY_HEURE_UPDATE
from .helpers import curtailment_signal_key, is_bridage_active, parse_heure_update

_LOGGER = logging.getLogger(__name__)


class ThreeERLApiError(Exception):
    """Exception raised when the 3ERL API request fails."""


class ThreeERLApiClient:
    """Async client for the public 3ERL API.

    :param session: aiohttp client session.
    :type session: aiohttp.ClientSession
    :param api_url: Full URL to the 3ERL JSON endpoint.
    :type api_url: str
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_url: str,
        aggregation_mode: str = DEFAULT_AGGREGATION_MODE,
    ) -> None:
        """Initialize the 3ERL API client."""
        self._session = session
        self._api_url = api_url
        self._aggregation_mode = aggregation_mode

    async def fetch(self) -> dict[str, Any]:
        """Fetch the latest data from the 3ERL API.

        :return: Parsed JSON response from the API.
        :rtype: dict[str, Any]
        :raises ThreeERLApiError: If the request fails or the response is invalid.
        """
        _LOGGER.debug("Fetching 3ERL data from %s", self._api_url)
        try:
            async with asyncio.timeout(API_TIMEOUT_SECONDS):
                async with self._session.get(self._api_url) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except aiohttp.ClientResponseError as err:
            raise ThreeERLApiError(f"3ERL API request failed: {err.status} {err.message}") from err
        except aiohttp.ClientError as err:
            raise ThreeERLApiError(f"3ERL API connection error: {err}") from err
        except TimeoutError as err:
            raise ThreeERLApiError("3ERL API request timed out") from err
        except ValueError as err:
            raise ThreeERLApiError(f"3ERL API returned invalid JSON: {err}") from err

        if not isinstance(data, dict):
            raise ThreeERLApiError("3ERL API returned an unexpected response type")

        if is_bridage_active(data, self._aggregation_mode) is None:
            signal_key = curtailment_signal_key(self._aggregation_mode)
            raise ThreeERLApiError(f"3ERL API returned an invalid {signal_key} signal")
        published = parse_heure_update(data.get(SENSOR_KEY_HEURE_UPDATE))
        if published is None or published > dt_util.utcnow():
            raise ThreeERLApiError("3ERL API returned an invalid or future Heure_Update")
        return data
