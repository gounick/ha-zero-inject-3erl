"""The 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ThreeERLApiClient, ThreeERLApiError
from .const import CONF_API_URL, DEFAULT_API_URL, DOMAIN, SERVICE_RESET_COUNTERS
from .controller import ZeroInjectController
from .coordinator import ThreeERLUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 3ERL Zero-Injection from a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :return: True if setup succeeded.
    :rtype: bool
    """
    session = async_get_clientsession(hass)
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    api = ThreeERLApiClient(session, api_url)

    coordinator = ThreeERLUpdateCoordinator(hass, api, entry)
    try:
        await coordinator.async_load_cumulative_data()
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    except ThreeERLApiError as err:
        raise ConfigEntryNotReady(f"Unable to connect to 3ERL API: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "entry": entry,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    controller = ZeroInjectController(hass, entry, coordinator)
    await controller.async_setup()
    hass.data[DOMAIN][entry.entry_id]["controller"] = controller

    _register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


def _register_services(hass: HomeAssistant) -> None:
    """Register integration-wide services.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    """

    async def async_handle_reset_counters(call: ServiceCall) -> None:
        """Handle the reset_counters service.

        :param call: Service call data.
        :type call: ServiceCall
        """
        for entry_data in hass.data.get(DOMAIN, {}).values():
            coordinator = entry_data.get("coordinator")
            if isinstance(coordinator, ThreeERLUpdateCoordinator):
                await coordinator.async_reset_counters()

    if not hass.services.has_service(DOMAIN, SERVICE_RESET_COUNTERS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_COUNTERS,
            async_handle_reset_counters,
        )


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Updated config entry.
    :type entry: ConfigEntry
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being unloaded.
    :type entry: ConfigEntry
    :return: True if unload succeeded.
    :rtype: bool
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        controller = hass.data[DOMAIN][entry.entry_id].get("controller")
        if controller is not None:
            await controller.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
