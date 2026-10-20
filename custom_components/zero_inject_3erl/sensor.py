"""Sensor platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ThreeERLConfigEntry
from .const import (
    SENSOR_KEY_BRIDAGE_LONG_TERME,
    SENSOR_KEY_COMMENTAIRES,
    SENSOR_KEY_DERNIER_PREP,
    SENSOR_KEY_HEURE_UPDATE,
    SENSOR_KEY_MODE_DEGRADE,
    SENSOR_KEY_PRD4,
    SENSOR_KEY_PREP_PROFILE,
    SENSOR_KEY_PREP_PROFILE_NUM,
    SENSOR_KEY_RTE_INDISPO_DEPUIS,
)
from .entity import ThreeERLEntity

CURRENCY_CODE = "EUR"
PRICE_UNIT = "€/MWh"

DataFn = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class ThreeERLSensorEntityDescription(SensorEntityDescription):
    """Describe a 3ERL sensor and how to read its value from coordinator data."""

    value_fn: DataFn
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _api(key: str) -> DataFn:
    """Return a reader for a raw 3ERL API field.

    :param key: API response key.
    :type key: str
    :return: Function reading the field from coordinator data.
    :rtype: DataFn
    """
    return lambda data: data.get("api_data", {}).get(key)


def _computed(key: str) -> DataFn:
    """Return a reader for a value computed by the coordinator.

    :param key: Coordinator data key.
    :type key: str
    :return: Function reading the value from coordinator data.
    :rtype: DataFn
    """
    return lambda data: data.get(key)


def _price(key: str, translation_key: str, value_fn: DataFn) -> ThreeERLSensorEntityDescription:
    """Return the description of a price sensor in EUR/MWh.

    :param key: Unique id suffix.
    :type key: str
    :param translation_key: Translation key of the entity name.
    :type translation_key: str
    :param value_fn: Function reading the value.
    :type value_fn: DataFn
    :return: Sensor description.
    :rtype: ThreeERLSensorEntityDescription
    """
    return ThreeERLSensorEntityDescription(
        key=key,
        translation_key=translation_key,
        native_unit_of_measurement=PRICE_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=value_fn,
    )


def _text(key: str, translation_key: str, **kwargs: Any) -> ThreeERLSensorEntityDescription:
    """Return the description of a raw API sensor without unit.

    :param key: API response key, also used as unique id suffix.
    :type key: str
    :param translation_key: Translation key of the entity name.
    :type translation_key: str
    :return: Sensor description.
    :rtype: ThreeERLSensorEntityDescription
    """
    return ThreeERLSensorEntityDescription(
        key=key, translation_key=translation_key, value_fn=_api(key), **kwargs
    )


SENSORS: tuple[ThreeERLSensorEntityDescription, ...] = (
    _price(SENSOR_KEY_DERNIER_PREP, "latest_prep", _api(SENSOR_KEY_DERNIER_PREP)),
    _price(SENSOR_KEY_PRD4, "prd4", _api(SENSOR_KEY_PRD4)),
    _price(SENSOR_KEY_PREP_PROFILE_NUM, "prep_profile_num", _api(SENSOR_KEY_PREP_PROFILE_NUM)),
    _price("current_prep", "current_prep", _computed("current_prep")),
    _price("estimated_daily_prep", "estimated_daily_prep", _computed("estimated_daily_prep")),
    _text(
        SENSOR_KEY_PREP_PROFILE,
        "daily_trend",
        attributes_fn=lambda data: {
            "heure_update": data.get("api_data", {}).get(SENSOR_KEY_HEURE_UPDATE)
        },
    ),
    _text(SENSOR_KEY_HEURE_UPDATE, "last_update"),
    _text(SENSOR_KEY_BRIDAGE_LONG_TERME, "long_term_curtailment"),
    _text(SENSOR_KEY_MODE_DEGRADE, "degraded_mode"),
    _text(SENSOR_KEY_RTE_INDISPO_DEPUIS, "rte_unavailable_since"),
    _text(SENSOR_KEY_COMMENTAIRES, "comments"),
    ThreeERLSensorEntityDescription(
        key="puissance_bridable",
        translation_key="curtailable_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_computed("puissance_bridable"),
    ),
    ThreeERLSensorEntityDescription(
        key="puissance_gain",
        translation_key="gain_rate",
        native_unit_of_measurement="€/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_computed("puissance_gain"),
    ),
    ThreeERLSensorEntityDescription(
        key="energie_bridage_kwh",
        translation_key="curtailed_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_computed("energie_bridage_kwh"),
    ),
    ThreeERLSensorEntityDescription(
        key="gain_cumule_eur",
        translation_key="cumulative_gain",
        native_unit_of_measurement=CURRENCY_CODE,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_computed("gain_cumule_eur"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensor entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ThreeERLConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    coordinator = entry.runtime_data.coordinator
    async_add_entities(ThreeERLSensor(coordinator, description) for description in SENSORS)


class ThreeERLSensor(ThreeERLEntity, SensorEntity):
    """Sensor reading its value from the coordinator data."""

    entity_description: ThreeERLSensorEntityDescription

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes when the description defines them."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data or {})
