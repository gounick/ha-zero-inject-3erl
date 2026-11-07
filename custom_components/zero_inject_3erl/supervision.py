import math
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from . import ThreeERLConfigEntry
from .const import (
    CONF_INJECTION_DELAY,
    CONF_INJECTION_MAX_AGE,
    CONF_INJECTION_POWER_ENTITY,
    CONF_INJECTION_THRESHOLD,
    DEFAULT_INJECTION_DELAY,
    DEFAULT_INJECTION_MAX_AGE,
    DEFAULT_INJECTION_THRESHOLD,
    DOMAIN,
    RELAY_FAULT_DELAY,
    SUPERVISION_INTERVAL,
)
from .helpers import (
    build_device_info,
    entry_settings,
    get_bypass_entity_id,
    get_mode_entity_id,
    relay_entities,
)


class ThreeERLSupervisionSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(self, entry: ThreeERLConfigEntry, key: str) -> None:
        self._entry = entry
        self._controller = entry.runtime_data.controller
        self._settings = entry_settings(entry)
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{key}"
        self._attr_device_info = build_device_info(entry.entry_id)
        self._since: dict[str, datetime] = {}
        self._last_command: bool | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        tracked = relay_entities(self._settings)
        for entity_id in (
            get_mode_entity_id(self.hass, self._entry.entry_id),
            get_bypass_entity_id(self.hass, self._entry.entry_id),
            self._settings.get(CONF_INJECTION_POWER_ENTITY),
        ):
            if entity_id:
                tracked.append(entity_id)
        self.async_on_remove(async_track_state_change_event(self.hass, tracked, self._update))
        self.async_on_remove(
            async_track_time_interval(self.hass, self._update, SUPERVISION_INTERVAL)
        )
        self.async_on_remove(self._entry.runtime_data.coordinator.async_add_listener(self._update))
        self._update()

    @callback
    def _update(self, event=None) -> None:
        active = self._controller.commanded_active
        if active != self._last_command:
            self._since.clear()
            self._last_command = active
        self._attr_extra_state_attributes = {
            "commanded_limitation": active,
            "manual_bypass": self._controller.bypassed,
        }
        if self._key == "relay_control_fault":
            self._update_relay_fault(active)
        else:
            self._update_injection(active)
        self.async_write_ha_state()

    def _update_relay_fault(self, active: bool | None) -> None:
        states = {
            entity_id: self.hass.states.get(entity_id)
            for entity_id in relay_entities(self._settings)
        }
        unavailable = [
            entity_id
            for entity_id, state in states.items()
            if state is None or state.state not in ("on", "off")
        ]
        misaligned = [
            entity_id
            for entity_id, state in states.items()
            if not self._controller.bypassed
            and active is not None
            and state is not None
            and state.state in ("on", "off")
            and (state.state == "on") != active
        ]
        self._attr_extra_state_attributes.update(
            unavailable_relays=unavailable,
            misaligned_relays=misaligned,
            relay_states={
                entity_id: state.state if state else "missing"
                for entity_id, state in states.items()
            },
        )
        if self._controller.bypassed or active is None:
            self._since.clear()
            self._attr_is_on = False if self._controller.bypassed else None
            self._attr_extra_state_attributes["reason"] = (
                "manual_bypass" if self._controller.bypassed else "no_signal"
            )
            return
        now = dt_util.utcnow()
        self._since = {entity_id: self._since.get(entity_id, now) for entity_id in misaligned}
        self._attr_is_on = bool(unavailable) or any(
            now - since >= RELAY_FAULT_DELAY for since in self._since.values()
        )
        self._attr_extra_state_attributes["reason"] = (
            "unavailable"
            if unavailable
            else "misaligned"
            if self._attr_is_on
            else "aligned_or_settling"
        )

    def _read_injection(self) -> tuple[float | None, str]:
        entity_id = self._settings.get(CONF_INJECTION_POWER_ENTITY)
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is None:
            return None, "missing_measurement"
        max_age = self._settings.get(CONF_INJECTION_MAX_AGE, DEFAULT_INJECTION_MAX_AGE)
        age = (dt_util.utcnow() - state.last_reported).total_seconds()
        self._attr_extra_state_attributes.update(
            source_entity=entity_id, measurement_timestamp=state.last_reported.isoformat()
        )
        if age > max_age or age < 0:
            return None, "stale_measurement"
        unit = state.attributes.get("unit_of_measurement")
        scale = {"W": 1, "kW": 1000, "VA": 1, "kVA": 1000}.get(unit)
        if scale is None:
            return None, "unsupported_unit"
        try:
            value = float(state.state) * scale
        except ValueError, TypeError:
            return None, "invalid_measurement"
        if not math.isfinite(value) or value < 0:
            return None, "invalid_measurement"
        self._attr_extra_state_attributes.update(
            measured_export=value, measurement_unit="VA" if unit in ("VA", "kVA") else "W"
        )
        return value, "valid_measurement"

    def _update_injection(self, active: bool | None) -> None:
        value, reason = self._read_injection()
        threshold = self._settings.get(CONF_INJECTION_THRESHOLD, DEFAULT_INJECTION_THRESHOLD)
        delay = self._settings.get(CONF_INJECTION_DELAY, DEFAULT_INJECTION_DELAY)
        self._attr_extra_state_attributes.update(threshold=threshold, delay_seconds=delay)
        if value is None or active is None:
            self._since.clear()
            self._attr_is_on = None
        elif not active or value <= threshold:
            self._since.clear()
            self._attr_is_on = False
            reason = "no_commanded_limitation" if not active else "no_export_observed"
        else:
            since = self._since.setdefault("export", dt_util.utcnow())
            self._attr_is_on = dt_util.utcnow() - since >= timedelta(seconds=delay)
            reason = "export_observed" if self._attr_is_on else "settling"
        self._attr_extra_state_attributes["reason"] = reason
