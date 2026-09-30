"""Sensor platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_KEY_BRIDAGE_LONG_TERME,
    SENSOR_KEY_COMMENTAIRES,
    SENSOR_KEY_DERNIER_PREP,
    SENSOR_KEY_HEURE_UPDATE,
    SENSOR_KEY_MODE_DEGRADE,
    SENSOR_KEY_PRD4,
    SENSOR_KEY_PREP_PROFILE,
    SENSOR_KEY_RTE_INDISPO_DEPUIS,
)
from .coordinator import ThreeERLUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _api_value(coordinator: ThreeERLUpdateCoordinator, key: str, default: Any = None) -> Any:
    """Return a value from the latest 3ERL API response.

    :param coordinator: 3ERL data coordinator.
    :type coordinator: ThreeERLUpdateCoordinator
    :param key: API response key.
    :type key: str
    :param default: Default value if not found.
    :type default: Any
    :return: Value from the API response or default.
    :rtype: Any
    """
    if not coordinator.data:
        return default
    return coordinator.data.get("api_data", {}).get(key, default)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensor entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    coordinator: ThreeERLUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = [
        ThreeERLApiSensor(
            coordinator,
            "Dernier PRE+",
            SENSOR_KEY_DERNIER_PREP,
            "€/MWh",
            SensorDeviceClass.MONETARY,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Estimation jour PRD4",
            SENSOR_KEY_PRD4,
            "€/MWh",
            SensorDeviceClass.MONETARY,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Tendance du jour",
            SENSOR_KEY_PREP_PROFILE,
            None,
            None,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Heure update",
            SENSOR_KEY_HEURE_UPDATE,
            None,
            None,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Bridage long terme",
            SENSOR_KEY_BRIDAGE_LONG_TERME,
            "h",
            None,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Mode degrade",
            SENSOR_KEY_MODE_DEGRADE,
            None,
            None,
        ),
        ThreeERLApiSensor(
            coordinator,
            "RTE indispo depuis",
            SENSOR_KEY_RTE_INDISPO_DEPUIS,
            None,
            None,
        ),
        ThreeERLApiSensor(
            coordinator,
            "Commentaires",
            SENSOR_KEY_COMMENTAIRES,
            None,
            None,
        ),
        ThreeERLComputedSensor(
            coordinator,
            "Puissance bridable",
            "puissance_bridable",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
        ),
        ThreeERLComputedSensor(
            coordinator,
            "Puissance gain",
            "puissance_gain",
            "€/h",
            None,
            SensorStateClass.MEASUREMENT,
        ),
        ThreeERLComputedSensor(
            coordinator,
            "Énergie bridage",
            "energie_bridage_kwh",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        ),
        ThreeERLComputedSensor(
            coordinator,
            "Gain cumulé",
            "gain_cumule_eur",
            "€",
            SensorDeviceClass.MONETARY,
            SensorStateClass.TOTAL_INCREASING,
        ),
    ]

    async_add_entities(entities)


class ThreeERLBaseSensor(CoordinatorEntity[ThreeERLUpdateCoordinator], SensorEntity):
    """Base class for 3ERL sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ThreeERLUpdateCoordinator,
        name: str,
        unique_id_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{coordinator.config_entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="3ERL Zero-Injection",
            manufacturer="3ERL",
            model="Zero-Injection",
            configuration_url="https://3erl.fr",
        )


class ThreeERLApiSensor(ThreeERLBaseSensor):
    """Sensor exposing a raw value from the 3ERL API."""

    def __init__(
        self,
        coordinator: ThreeERLUpdateCoordinator,
        name: str,
        api_key: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize the API sensor."""
        super().__init__(coordinator, name, api_key)
        self._api_key = api_key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if device_class is not None and unit is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Any:
        """Return the latest API value."""
        return _api_value(self.coordinator, self._api_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for trend sensor."""
        attrs: dict[str, Any] = {}
        if self._api_key == SENSOR_KEY_PREP_PROFILE:
            heure = _api_value(self.coordinator, SENSOR_KEY_HEURE_UPDATE)
            if heure is not None:
                attrs["heure_update"] = heure
        return attrs


class ThreeERLComputedSensor(ThreeERLBaseSensor):
    """Sensor exposing a computed value from the coordinator."""

    def __init__(
        self,
        coordinator: ThreeERLUpdateCoordinator,
        name: str,
        data_key: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the computed sensor."""
        super().__init__(coordinator, name, data_key)
        self._data_key = data_key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self) -> Any:
        """Return the computed value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)
