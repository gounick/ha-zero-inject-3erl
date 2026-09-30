"""Tests for the 3ERL API client."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.zero_inject_3erl.api import ThreeERLApiClient, ThreeERLApiError


def _sample_api_response() -> dict[str, Any]:
    """Return a sample 3ERL API response."""
    return {
        "Bridage": 1,
        "Bridage_CDC": 0,
        "Dernier_PREP": 150.5,
        "Heure_Update": "30/09/2026 15:00",
        "PREP_Profile": "1+",
        "PRD4": 120.25,
        "Bridage_Long_Terme": 0,
    }


def _mock_aiohttp_response(
    json_data: Any | None = None,
    status: int = 200,
    text: str = "",
    raise_for_status: bool = True,
) -> MagicMock:
    """Return a mocked aiohttp response for use in an async context manager."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.text = AsyncMock(return_value=text)
    mock_resp.raise_for_status = MagicMock()
    if not raise_for_status:
        mock_resp.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=status,
            message="Server Error",
        )
    return mock_resp


def _mock_session_with_response(mock_resp: MagicMock) -> MagicMock:
    """Return a mocked aiohttp ClientSession that yields the given response."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_resp)
    cm.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get.return_value = cm
    return mock_session


async def test_fetch_success() -> None:
    """Test a successful API fetch."""
    mock_resp = _mock_aiohttp_response(json_data=_sample_api_response())
    mock_session = _mock_session_with_response(mock_resp)

    api = ThreeERLApiClient(mock_session, "https://3erl.fr/api.json")
    data = await api.fetch()

    assert data["Bridage"] == 1
    assert data["Dernier_PREP"] == 150.5
    assert data["PREP_Profile"] == "1+"


async def test_fetch_server_error() -> None:
    """Test that a server error raises ThreeERLApiError."""
    mock_resp = _mock_aiohttp_response(status=500, raise_for_status=False)
    mock_session = _mock_session_with_response(mock_resp)

    api = ThreeERLApiClient(mock_session, "https://3erl.fr/api.json")
    with pytest.raises(ThreeERLApiError):
        await api.fetch()


async def test_fetch_invalid_json() -> None:
    """Test that an invalid JSON response raises ThreeERLApiError."""
    mock_resp = _mock_aiohttp_response(json_data=None)
    mock_resp.json = AsyncMock(
        side_effect=aiohttp.ContentTypeError(
            request_info=MagicMock(),
            history=(),
            message="Invalid JSON",
        )
    )
    mock_session = _mock_session_with_response(mock_resp)

    api = ThreeERLApiClient(mock_session, "https://3erl.fr/api.json")
    with pytest.raises(ThreeERLApiError):
        await api.fetch()
