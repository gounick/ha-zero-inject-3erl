"""Binary sensor platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import ThreeERLConfigEntry
from .const import SENSOR_KEY_BRIDAGE, SENSOR_KEY_BRIDAGE_CDC
from .coordinator import ThreeERLUpdateCoordinator
from .entity import ThreeERLEntity
from .helpers import (
    compute_zero_inject_active,
    get_current_mode,
    get_mode_entity_id,
    is_flag_set,
)

API_FLAGS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(key=SENSOR_KEY_BRIDAGE, translation_key="curtailment_requested"),
    BinarySensorEntityDescription(
        key=SENSOR_KEY_BRIDAGE_CDC, translation_key="cdc_curtailment_requested"
    ),
)

ACTIVE_DESCRIPTION = BinarySensorEntityDescription(
    key="zero_inject_active",
    translation_key="zero_inject_active",
    device_class=BinarySensorDeviceClass.RUNNING,
)

STALE_DESCRIPTION = BinarySensorEntityDescription(
    key="data_stale",
    translation_key="data_stale",
    device_class=BinarySensorDeviceClass.PROBLEM,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create binary sensor entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ThreeERLConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        ThreeERLApiBinarySensor(coordinator, description) for description in API_FLAGS
    ]
    entities.append(ThreeERLActiveBinarySensor(coordinator))
    entities.append(ThreeERLStaleBinarySensor(coordinator))
    async_add_entities(entities)


class ThreeERLApiBinarySensor(ThreeERLEntity, BinarySensorEntity):
    """Binary sensor reflecting a boolean flag from the 3ERL API."""

    @property
    def is_on(self) -> bool | None:
        """Return True when the API flag is active."""
        if not self.coordinator.data:
            return None
        api_data = self.coordinator.data.get("api_data", {})
        return is_flag_set(api_data.get(self.entity_description.key))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the description slug of the sensor."""
        return {"description": self.entity_description.translation_key}


class ThreeERLActiveBinarySensor(ThreeERLEntity, BinarySensorEntity):
    """Binary sensor reflecting whether zero-injection is currently active."""

    def __init__(self, coordinator: ThreeERLUpdateCoordinator) -> None:
        """Initialize the active state binary sensor."""
        super().__init__(coordinator, ACTIVE_DESCRIPTION)
        self._mode_entity_id: str | None = None

    async def async_added_to_hass(self) -> None:
        """Track the mode select so the state follows mode changes."""
        await super().async_added_to_hass()
        self._mode_entity_id = get_mode_entity_id(self.hass, self.coordinator.config_entry.entry_id)
        if self._mode_entity_id is not None:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._mode_entity_id], self._on_mode_change
                )
            )

    @callback
    def _on_mode_change(self, event: Event) -> None:
        """Write the new state when the mode select changes."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return True when zero-injection should be active."""
        mode = get_current_mode(self.hass, self._mode_entity_id)
        return compute_zero_inject_active(mode, self.coordinator.curtailment_requested)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the reason for the current active state."""
        mode = get_current_mode(self.hass, self._mode_entity_id)
        reason = "No curtailment requested by 3ERL"
        if mode == "On":
            reason = "Forced ON (manual override)"
        elif mode == "Off":
            reason = "Forced OFF (manual override)"
        elif self.coordinator.curtailment_requested:
            reason = "Curtailment active - 3ERL signal"

        return {"mode": mode, "reason": reason, "description": "zero_inject_active"}


class ThreeERLStaleBinarySensor(ThreeERLEntity, BinarySensorEntity):
    """Binary sensor flagging 3ERL data older than two publication cycles.

    A stale signal may no longer reflect the current curtailment demand; the
    relay keeps following the last known state until fresh data arrives.
    """

    def __init__(self, coordinator: ThreeERLUpdateCoordinator) -> None:
        """Initialize the stale data binary sensor."""
        super().__init__(coordinator, STALE_DESCRIPTION)

    @property
    def is_on(self) -> bool | None:
        """Return True when the API data is stale."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("data_stale")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the data age and the description slug."""
        data = self.coordinator.data or {}
        return {
            "data_age_minutes": data.get("data_age_minutes"),
            "description": "data_stale",
        }
