"""The 3ERL Zero-Injection integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .api import ThreeERLApiClient
from .const import (
    CONF_AGGREGATION_MODE,
    CONF_API_URL,
    DEFAULT_AGGREGATION_MODE,
    DEFAULT_API_URL,
    DOMAIN,
    MODE_UNIQUE_ID_SUFFIX,
)
from .controller import ZeroInjectController
from .coordinator import ThreeERLPricingCoordinator, ThreeERLUpdateCoordinator
from .helpers import entry_settings
from .visibility import sync_contract_visibility

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
# The mode select is set up first so other entities can resolve its entity id.
DEPENDENT_PLATFORMS = [
    platform for platform in PLATFORMS if platform not in (Platform.SELECT, Platform.SWITCH)
]


@dataclass
class ThreeERLRuntimeData:
    """Objects owned by a loaded config entry."""

    coordinator: ThreeERLUpdateCoordinator
    controller: ZeroInjectController
    pricing_coordinator: ThreeERLPricingCoordinator


type ThreeERLConfigEntry = ConfigEntry[ThreeERLRuntimeData]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate entity identifiers and remove obsolete energy settings.

    :param hass: Home Assistant instance.
    :param entry: Config entry to migrate.
    :return: Whether the entry version is supported.
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
    if entry.minor_version < 3:
        removed = {"pv_power_entity", "consumption_power_entity"}
        hass.config_entries.async_update_entry(
            entry,
            data={key: value for key, value in entry.data.items() if key not in removed},
            options={key: value for key, value in entry.options.items() if key not in removed},
            minor_version=3,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> bool:
    """Set up signal control before starting informational pricing.

    :param hass: Home Assistant instance.
    :param entry: Config entry being set up.
    :return: True after local controls are available.
    """
    session = async_get_clientsession(hass)
    settings = entry_settings(entry)
    api_url = settings.get(CONF_API_URL, DEFAULT_API_URL)
    contract = settings.get(CONF_AGGREGATION_MODE, DEFAULT_AGGREGATION_MODE)
    coordinator = ThreeERLUpdateCoordinator(
        hass, ThreeERLApiClient(session, api_url, contract), entry
    )
    await coordinator.async_refresh()
    controller = ZeroInjectController(hass, entry, coordinator)
    pricing = ThreeERLPricingCoordinator(hass, session, entry)
    entry.runtime_data = ThreeERLRuntimeData(coordinator, controller, pricing)

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SELECT, Platform.SWITCH])
    await hass.config_entries.async_forward_entry_setups(entry, DEPENDENT_PLATFORMS)
    sync_contract_visibility(hass, entry, coordinator.aggregation_mode)
    await controller.async_setup()
    task = hass.async_create_background_task(pricing.async_refresh(), f"{DOMAIN}_initial_pricing")

    @callback
    def _cancel_pricing() -> None:
        task.cancel()

    entry.async_on_unload(_cancel_pricing)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> None:
    """Reload the config entry when options change.

    :param hass: Home Assistant instance.
    :param entry: Updated config entry.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> bool:
    """Unload the platforms and stop relay control.

    :param hass: Home Assistant instance.
    :param entry: Config entry being unloaded.
    :return: Whether all platforms were unloaded.
    """
    await entry.runtime_data.controller.async_shutdown()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        await entry.runtime_data.controller.async_setup()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ThreeERLConfigEntry) -> None:
    """Remove obsolete cumulative storage left by older development versions.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being removed.
    :type entry: ThreeERLConfigEntry
    """
    await Store(hass, 1, f"{DOMAIN}.cumulative_{entry.entry_id}").async_remove()
