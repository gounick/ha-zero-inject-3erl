"""Shared helpers for zero-injection logic."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    AGGREGATION_MODE_ACC,
    API_FALLBACK_INTERVAL,
    API_POLL_MARGIN,
    API_PUBLICATION_DELAY,
    API_RETRY_INTERVAL,
    API_TIME_FORMAT,
    API_TIMEZONE,
    CONF_RELAY_ENTITY,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_ZERO_INJECT_MODE,
    DOMAIN,
    MODE_UNIQUE_ID_SUFFIX,
    SENSOR_KEY_BRIDAGE,
    SENSOR_KEY_BRIDAGE_CDC,
    ZERO_INJECT_MODES,
)

_LOGGER = logging.getLogger(__name__)

# Flag values seen so far that did not match a known pattern. Logged once
# per distinct value to avoid spamming the log on every poll cycle.
_REPORTED_FLAG_VALUES: set[str] = set()


def entry_settings(entry: ConfigEntry) -> Mapping[str, Any]:
    """Return the active settings of a config entry.

    The options flow always saves the full set of settings, so once options
    exist they replace the initial data. This lets users clear optional fields.

    :param entry: Config entry to read.
    :type entry: ConfigEntry
    :return: Options if any were saved, otherwise the initial data.
    :rtype: Mapping[str, Any]
    """
    return entry.options or entry.data


def entity_id_list(settings: Mapping[str, Any], key: str) -> list[str]:
    """Return the entity ids stored under a multi-entity setting.

    The config flow stores these settings as lists. Entries created before
    multi-entity support may hold a single entity id string; it is
    normalized to a one-element list.

    :param settings: Active settings of a config entry.
    :type settings: Mapping[str, Any]
    :param key: Setting key to read.
    :type key: str
    :return: Entity ids configured for the setting.
    :rtype: list[str]
    """
    value = settings.get(key)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [entity_id for entity_id in value if isinstance(entity_id, str)]
    return []


def relay_entities(settings: Mapping[str, Any]) -> list[str]:
    """Return the configured zero-injection relay entity ids.

    :param settings: Active settings of a config entry.
    :type settings: Mapping[str, Any]
    :return: Entity ids of the relay switches to drive.
    :rtype: list[str]
    """
    return entity_id_list(settings, CONF_RELAY_ENTITY)


def build_device_info(entry_id: str) -> DeviceInfo:
    """Return the device shared by all entities of a config entry.

    :param entry_id: Config entry id.
    :type entry_id: str
    :return: Device information.
    :rtype: DeviceInfo
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="3ERL Zero-Injection",
        manufacturer="gounick",
        model="Zero-Injection",
        configuration_url="https://github.com/gounick/ha-zero-inject-3erl",
    )


def curtailment_signal_key(aggregation_mode: str = DEFAULT_AGGREGATION_MODE) -> str:
    """Return the 3ERL API field that carries the curtailment signal.

    :param aggregation_mode: Self-consumption contract type (aci or acc).
    :type aggregation_mode: str
    :return: The API key to read (Bridage for ACI, Bridage_CDC for ACC).
    :rtype: str
    """
    if aggregation_mode == AGGREGATION_MODE_ACC:
        return SENSOR_KEY_BRIDAGE_CDC
    return SENSOR_KEY_BRIDAGE


def is_bridage_active(
    api_data: dict[str, Any],
    aggregation_mode: str = DEFAULT_AGGREGATION_MODE,
) -> bool | None:
    """Return the curtailment signal, or None when invalid.

    :param api_data: Raw data returned by the 3ERL API.
    :type api_data: dict[str, Any]
    :param aggregation_mode: Self-consumption contract type (aci or acc).
    :type aggregation_mode: str
    :return: True when curtailment is requested.
    :rtype: bool
    """
    return is_flag_set(api_data.get(curtailment_signal_key(aggregation_mode)))


def is_flag_set(value: Any) -> bool | None:
    """Return whether a 3ERL API boolean flag is set.

    Known truthy values are 1, "1" and true/on/yes; known falsy values are
    0, "0" and false/off/no. Other values are unknown, never an off command.

    :param value: Raw flag value from the API.
    :type value: Any
    :return: True for 1 or a truthy string (true, on, yes).
    :rtype: bool
    """
    lowered = str(value).lower()
    if isinstance(value, bool | int | float | str):
        if value == 1 or lowered in ("1", "true", "on", "yes"):
            return True
        if value == 0 or lowered in ("0", "false", "off", "no"):
            return False
    reported = repr(value)
    if reported not in _REPORTED_FLAG_VALUES:
        if len(_REPORTED_FLAG_VALUES) >= 100:
            _REPORTED_FLAG_VALUES.clear()
        _REPORTED_FLAG_VALUES.add(reported)
        _LOGGER.warning("Unexpected 3ERL flag value %r, treated as unknown", value)
    return None


def get_mode_entity_id(hass: HomeAssistant, entry_id: str) -> str | None:
    """Return the entity id of the mode select of a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry_id: Config entry id.
    :type entry_id: str
    :return: Entity id of the mode select, or None if not registered.
    :rtype: str | None
    """
    return er.async_get(hass).async_get_entity_id("select", DOMAIN, mode_unique_id(entry_id))


def get_bypass_entity_id(hass: HomeAssistant, entry_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{DOMAIN}_{entry_id}_manual_bypass"
    )


def is_manual_bypass(hass: HomeAssistant, entry_id: str) -> bool:
    entity_id = get_bypass_entity_id(hass, entry_id)
    return entity_id is not None and hass.states.is_state(entity_id, "on")


def mode_unique_id(entry_id: str) -> str:
    """Return the unique id of the mode select of a config entry.

    :param entry_id: Config entry id.
    :type entry_id: str
    :return: Unique id, prefixed with the domain like every other entity.
    :rtype: str
    """
    return f"{DOMAIN}_{entry_id}_{MODE_UNIQUE_ID_SUFFIX}"


def parse_heure_update(heure_update: Any) -> datetime | None:
    """Parse the ``Heure_Update`` field of the 3ERL API.

    :param heure_update: ``Heure_Update`` value (dd/mm/YYYY HH:MM, Paris time).
    :type heure_update: Any
    :return: Aware publication time, or None when unparseable.
    :rtype: datetime | None
    """
    try:
        return datetime.strptime(heure_update, API_TIME_FORMAT).replace(tzinfo=API_TIMEZONE)
    except TypeError, ValueError:
        return None


def next_poll_delay(heure_update: Any, now: datetime) -> timedelta:
    """Return the delay before the next 3ERL API poll.

    3ERL publishes new data about 18 minutes after ``Heure_Update`` and retries
    RTE every minute when data is late. Polling earlier returns the same data.

    :param heure_update: ``Heure_Update`` value from the API (dd/mm/YYYY HH:MM, Paris time).
    :type heure_update: Any
    :param now: Current timezone-aware time.
    :type now: datetime
    :return: Delay until the next expected publication, one minute when the
        data is late, or the fallback interval when the value is unparseable.
    :rtype: timedelta
    """
    published = parse_heure_update(heure_update)
    if published is None:
        return API_FALLBACK_INTERVAL
    now = now.astimezone(UTC)
    published = published.astimezone(UTC)
    if published > now:
        return API_RETRY_INTERVAL
    delay = published + API_PUBLICATION_DELAY + API_POLL_MARGIN - now
    return min(API_FALLBACK_INTERVAL, max(API_RETRY_INTERVAL, delay))


def get_current_mode(hass: HomeAssistant, mode_entity_id: str | None) -> str:
    """Return the current zero-injection mode from the select entity.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param mode_entity_id: Entity id of the mode select, or None.
    :type mode_entity_id: str | None
    :return: One of Auto, On, Off.
    :rtype: str
    """
    if mode_entity_id is None:
        return DEFAULT_ZERO_INJECT_MODE
    state = hass.states.get(mode_entity_id)
    if state is None or state.state not in ZERO_INJECT_MODES:
        return DEFAULT_ZERO_INJECT_MODE
    return state.state


def compute_commanded_limitation(mode: str, bridage_active: bool | None) -> bool | None:
    """Return whether zero-injection should be active.

    :param mode: Current zero-injection mode.
    :type mode: str
    :param bridage_active: Whether curtailment is requested by the API.
    :type bridage_active: bool
    :return: True when the relay should be turned on.
    :rtype: bool
    """
    if mode == "On":
        return True
    if mode == "Off":
        return False
    return bridage_active
