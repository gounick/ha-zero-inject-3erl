"""Shared helpers for zero-injection logic."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
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
    CONF_PV_POWER_ENTITY,
    CONF_RELAY_ENTITY,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_ZERO_INJECT_MODE,
    DOMAIN,
    MODE_UNIQUE_ID_SUFFIX,
    SENSOR_KEY_BRIDAGE,
    SENSOR_KEY_BRIDAGE_CDC,
    ZERO_INJECT_MODES,
)


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


def pv_power_entities(settings: Mapping[str, Any]) -> list[str]:
    """Return the configured PV production sensor entity ids.

    :param settings: Active settings of a config entry.
    :type settings: Mapping[str, Any]
    :return: Entity ids of the production sensors to sum.
    :rtype: list[str]
    """
    return entity_id_list(settings, CONF_PV_POWER_ENTITY)


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
        manufacturer="3ERL",
        model="Zero-Injection",
        configuration_url="https://3erl.fr",
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
) -> bool:
    """Return whether the 3ERL API requests curtailment.

    :param api_data: Raw data returned by the 3ERL API.
    :type api_data: dict[str, Any]
    :param aggregation_mode: Self-consumption contract type (aci or acc).
    :type aggregation_mode: str
    :return: True when curtailment is requested.
    :rtype: bool
    """
    return is_flag_set(api_data.get(curtailment_signal_key(aggregation_mode)))


def is_flag_set(value: Any) -> bool:
    """Return whether a 3ERL API boolean flag is set.

    :param value: Raw flag value from the API.
    :type value: Any
    :return: True for 1 or a truthy string (true, on, yes).
    :rtype: bool
    """
    return value == 1 or str(value).lower() in ("true", "on", "yes")


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


def mode_unique_id(entry_id: str) -> str:
    """Return the unique id of the mode select of a config entry.

    :param entry_id: Config entry id.
    :type entry_id: str
    :return: Unique id, prefixed with the domain like every other entity.
    :rtype: str
    """
    return f"{DOMAIN}_{entry_id}_{MODE_UNIQUE_ID_SUFFIX}"


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
    try:
        published = datetime.strptime(heure_update, API_TIME_FORMAT).replace(tzinfo=API_TIMEZONE)
    except TypeError, ValueError:
        return API_FALLBACK_INTERVAL
    next_publication = published + API_PUBLICATION_DELAY + API_POLL_MARGIN
    if next_publication <= now:
        return API_RETRY_INTERVAL
    return next_publication - now


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


def compute_zero_inject_active(mode: str, bridage_active: bool) -> bool:
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
