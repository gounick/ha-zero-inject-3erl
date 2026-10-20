"""Tests for the pricing data manager."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import aiohttp
import pytest

from custom_components.zero_inject_3erl.pricing import PricingDataError, PricingDataManager


def _mock_response(json_data: Any | None = None, status: int = 200) -> MagicMock:
    """Return a mocked aiohttp response for an async context manager."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_session(get_resp: MagicMock, post_resp: MagicMock) -> MagicMock:
    """Return a mocked aiohttp ClientSession that yields the given responses."""
    get_cm = AsyncMock()
    get_cm.__aenter__ = AsyncMock(return_value=get_resp)
    get_cm.__aexit__ = AsyncMock(return_value=False)

    post_cm = AsyncMock()
    post_cm.__aenter__ = AsyncMock(return_value=post_resp)
    post_cm.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get.return_value = get_cm
    mock_session.post.return_value = post_cm
    return mock_session


def _rte_response(base_slot: datetime) -> dict[str, Any]:
    """Return a minimal RTE PREP response covering one day."""
    values = []
    for i in range(96):
        slot = base_slot + timedelta(minutes=15 * i)
        values.append(
            {
                "date": slot.isoformat(),
                "pre": {"positive": str(100.0 + i)},
            }
        )
    return {"values": values}


def _enedis_response(base_slot: datetime) -> list[dict[str, Any]]:
    """Return a minimal Enedis PRD3 response covering one day."""
    values = []
    for i in range(96):
        slot = base_slot + timedelta(minutes=15 * i)
        values.append(
            {
                "horodate": slot.isoformat(),
                "coefficient_dynamique_j_1": 0.0004,
            }
        )
    return values


async def test_update_computes_estimated_daily_prep() -> None:
    """Test that the manager fetches data and computes the estimated daily PRE+."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    rte_base = datetime(2026, 10, 4, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    prd3_base = datetime(2026, 10, 2, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

    get_resp = _mock_response(json_data=_rte_response(rte_base))
    post_resp = _mock_response(json_data=_enedis_response(prd3_base))
    session = _mock_session(get_resp, post_resp)

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        manager = PricingDataManager(session)
        await manager.async_update()

        # With a constant PRD3 factor, the weighted average equals the simple
        # average of all PREP values seen so far.
        assert manager.estimated_daily_prep is not None
        assert manager.estimated_daily_prep == pytest.approx(147.5, rel=1e-6)

        # The current slot at 14:20 is 14:15, which is the 58th quarter-hour
        # (index 57, starting from 0 at 00:00).
        assert manager.current_prep() == pytest.approx(157.0, rel=1e-6)


async def test_update_falls_back_when_no_prd3_data() -> None:
    """Test that the estimated daily PRE+ is None when the PRD3 profile is empty."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    rte_base = datetime(2026, 10, 4, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

    get_resp = _mock_response(json_data=_rte_response(rte_base))
    post_resp = _mock_response(json_data=[])
    session = _mock_session(get_resp, post_resp)

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        manager = PricingDataManager(session)
        await manager.async_update()

        assert manager.estimated_daily_prep is None
        assert manager.current_prep() is not None


async def test_prd3_profile_is_fetched_once_per_day() -> None:
    """Test that the PRD3 profile is cached for the selected day."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    rte_base = datetime(2026, 10, 4, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    prd3_base = datetime(2026, 10, 2, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    session = _mock_session(
        _mock_response(json_data=_rte_response(rte_base)),
        _mock_response(json_data=_enedis_response(prd3_base)),
    )

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        manager = PricingDataManager(session)
        await manager.async_update()
        await manager.async_update()

    assert session.post.call_count == 1
    assert session.get.call_count == 2


async def test_enedis_json_is_parsed_despite_html_mimetype() -> None:
    """Test that the PRD3 body is decoded even with a text/html Content-Type."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    rte_base = datetime(2026, 10, 4, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    prd3_base = datetime(2026, 10, 2, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    post_resp = _mock_response(json_data=_enedis_response(prd3_base))
    session = _mock_session(_mock_response(json_data=_rte_response(rte_base)), post_resp)

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        manager = PricingDataManager(session)
        await manager.async_update()

    post_resp.json.assert_awaited_with(content_type=None)
    assert manager.estimated_daily_prep is not None


async def test_prd3_is_fetched_when_rte_fails() -> None:
    """Test that an RTE failure is raised without preventing the PRD3 fetch."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    prd3_base = datetime(2026, 10, 2, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    session = _mock_session(
        _mock_response(json_data=None),
        _mock_response(json_data=_enedis_response(prd3_base)),
    )
    session.get.return_value.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("down"))

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        manager = PricingDataManager(session)
        with pytest.raises(PricingDataError, match="Failed to fetch RTE"):
            await manager.async_update()

    assert session.post.call_count == 1
    assert manager._prd3_values


async def test_requests_use_client_timeout() -> None:
    """Test that requests pass an aiohttp ClientTimeout."""
    now = datetime(2026, 10, 4, 14, 20, tzinfo=ZoneInfo("Europe/Paris"))
    session = _mock_session(_mock_response(json_data={"values": []}), _mock_response(json_data=[]))

    with patch("custom_components.zero_inject_3erl.pricing.dt_now", return_value=now):
        await PricingDataManager(session).async_update()

    assert isinstance(session.get.call_args.kwargs["timeout"], aiohttp.ClientTimeout)
    assert isinstance(session.post.call_args.kwargs["timeout"], aiohttp.ClientTimeout)
