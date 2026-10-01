"""Binary sensor platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_KEY_BRIDAGE, SENSOR_KEY_BRIDAGE_CDC
from .coordinator import ThreeERLUpdateCoordinator
from .helpers import compute_zero_inject_active, get_current_mode, is_bridage_active

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create binary sensor entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    coordinator: ThreeERLUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            ThreeERLApiBinarySensor(
                coordinator,
                "Bridage demandé",
                SENSOR_KEY_BRIDAGE,
                "mdi:car-speed-limiter",
            ),
            ThreeERLApiBinarySensor(
                coordinator,
                "Bridage CDC demandé",
                SENSOR_KEY_BRIDAGE_CDC,
                "mdi:car-speed-limiter",
            ),
            ThreeERLActiveBinarySensor(coordinator),
        ]
    )


class ThreeERLBaseBinarySensor(CoordinatorEntity[ThreeERLUpdateCoordinator], BinarySensorEntity):
    """Base class for 3ERL binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ThreeERLUpdateCoordinator,
        name: str,
        unique_id_suffix: str,
        icon: str | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{coordinator.config_entry.entry_id}_{unique_id_suffix}"
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="3ERL Zero-Injection",
            manufacturer="3ERL",
            model="Zero-Injection",
            configuration_url="https://3erl.fr",
        )

    @property
    def available(self) -> bool:
        """Return whether the sensor is available."""
        return super().available and self.coordinator.last_update_success


class ThreeERLApiBinarySensor(ThreeERLBaseBinarySensor):
    """Binary sensor reflecting a boolean flag from the 3ERL API."""

    def __init__(
        self,
        coordinator: ThreeERLUpdateCoordinator,
        name: str,
        api_key: str,
        icon: str | None = None,
    ) -> None:
        """Initialize the API binary sensor."""
        super().__init__(coordinator, name, api_key, icon)
        self._api_key = api_key

    @property
    def is_on(self) -> bool | None:
        """Return True when the API flag is active."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get("api_data", {}).get(self._api_key)
        return value == 1 or str(value).lower() in ("true", "on", "yes")


class ThreeERLActiveBinarySensor(ThreeERLBaseBinarySensor):
    """Binary sensor reflecting whether zero-injection is currently active."""

    def __init__(self, coordinator: ThreeERLUpdateCoordinator) -> None:
        """Initialize the active state binary sensor."""
        super().__init__(coordinator, "Zero-Inject actif", "zero_inject_active")
        self._attr_device_class = "running"
        self._attr_icon = "mdi:flash-off"

    @property
    def is_on(self) -> bool | None:
        """Return True when zero-injection should be active."""
        mode = get_current_mode(self.hass, self._mode_entity_id())
        api_data = self.coordinator.data.get("api_data", {}) if self.coordinator.data else {}
        bridage_active = is_bridage_active(api_data, self.coordinator.aggregation_mode)
        return compute_zero_inject_active(mode, bridage_active)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the reason for the current active state."""
        mode = get_current_mode(self.hass, self._mode_entity_id())
        reason = "No curtailment requested by 3ERL"
        if mode == "On":
            reason = "Forced ON (manual override)"
        elif mode == "Off":
            reason = "Forced OFF (manual override)"
        elif is_bridage_active(
            self.coordinator.data.get("api_data", {}) if self.coordinator.data else {},
            self.coordinator.aggregation_mode,
        ):
            reason = "Curtailment active - 3ERL signal"

        return {"mode": mode, "reason": reason}

    def _mode_entity_id(self) -> str | None:
        """Resolve the mode select entity id for this config entry.

        :return: Entity id of the mode select, or None if not found.
        :rtype: str | None
        """
        registry = async_get_entity_registry(self.hass)
        expected_unique_id = f"{self.coordinator.config_entry.entry_id}_mode"
        for entity in registry.entities.values():
            if (
                entity.config_entry_id == self.coordinator.config_entry.entry_id
                and entity.domain == "select"
                and entity.unique_id == expected_unique_id
            ):
                return entity.entity_id
        return None
