"""The 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .api import ThreeERLApiClient
from .const import (
    CONF_API_URL,
    DEFAULT_API_URL,
    DOMAIN,
    MODE_UNIQUE_ID_SUFFIX,
    SERVICE_RESET_COUNTERS,
    STORAGE_KEY,
)
from .controller import ZeroInjectController
from .coordinator import ThreeERLUpdateCoordinator
from .helpers import entry_settings

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
]
# The mode select is set up first so other entities can resolve its entity id.
DEPENDENT_PLATFORMS = [platform for platform in PLATFORMS if platform is not Platform.SELECT]

RESET_COUNTERS_SCHEMA = vol.Schema(
    {
        vol.Optional("energy_kwh"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("gain_eur"): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)


@dataclass
class ThreeERLRuntimeData:
    """Objects owned by a loaded config entry."""

    coordinator: ThreeERLUpdateCoordinator
    controller: ZeroInjectController


type ThreeERLConfigEntry = ConfigEntry[ThreeERLRuntimeData]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration services.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param config: YAML configuration (unused, config entries only).
    :type config: ConfigType
    :return: True.
    :rtype: bool
    """

    async def async_handle_reset_counters(call: ServiceCall) -> None:
        """Reset the counters of every loaded config entry.

        Optional ``energy_kwh`` and ``gain_eur`` fields seed the counters
        instead of zeroing them, e.g. to match the 3ERL dashboard totals.

        :param call: Service call data.
        :type call: ServiceCall
        """
        entries: list[ThreeERLConfigEntry] = hass.config_entries.async_loaded_entries(DOMAIN)
        for entry in entries:
            await entry.runtime_data.coordinator.async_reset_counters(
                energy_kwh=call.data.get("energy_kwh"),
                gain_eur=call.data.get("gain_eur"),
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_COUNTERS,
        async_handle_reset_counters,
        schema=RESET_COUNTERS_SCHEMA,
    )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate a config entry to the current version.

    Minor version 2 prefixes the mode select unique id with the domain, like
    every other entity of the integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry to migrate.
    :type entry: ConfigEntry
    :return: True when the entry is at the current version.
    :rtype: bool
    """
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        legacy_unique_id = f"{entry.entry_id}_{MODE_UNIQUE_ID_SUFFIX}"

        @callback
        def _migrate_unique_id(entity: er.RegistryEntry) -> dict[str, str] | None:
            if entity.domain == Platform.SELECT and entity.unique_id == legacy_unique_id:
                return {"new_unique_id": f"{DOMAIN}_{legacy_unique_id}"}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)
        hass.config_entries.async_update_entry(entry, minor_version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> bool:
    """Set up 3ERL Zero-Injection from a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ThreeERLConfigEntry
    :return: True if setup succeeded.
    :rtype: bool
    """
    session = async_get_clientsession(hass)
    api_url = entry_settings(entry).get(CONF_API_URL, DEFAULT_API_URL)
    coordinator = ThreeERLUpdateCoordinator(
        hass, ThreeERLApiClient(session, api_url), session, entry
    )
    await coordinator.async_load_cumulative_data()
    await coordinator.async_config_entry_first_refresh()
    coordinator.start_power_tracking()

    controller = ZeroInjectController(hass, entry, coordinator)
    entry.runtime_data = ThreeERLRuntimeData(coordinator, controller)

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SELECT])
    await hass.config_entries.async_forward_entry_setups(entry, DEPENDENT_PLATFORMS)

    await controller.async_setup()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> None:
    """Reload the config entry when options change.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Updated config entry.
    :type entry: ThreeERLConfigEntry
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> bool:
    """Unload a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being unloaded.
    :type entry: ThreeERLConfigEntry
    :return: True if unload succeeded.
    :rtype: bool
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.controller.async_shutdown()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> None:
    """Remove the persisted cumulative data of a deleted config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being removed.
    :type entry: ThreeERLConfigEntry
    """
    await Store(hass, 1, f"{STORAGE_KEY}_{entry.entry_id}").async_remove()
