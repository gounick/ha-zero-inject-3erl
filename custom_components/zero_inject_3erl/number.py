"""Number platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ThreeERLConfigEntry
from .const import (
    BYPASS_DURATION_UNIQUE_ID_SUFFIX,
    DEFAULT_BYPASS_DURATION_MINUTES,
    DEFAULT_FORCED_MODE_DURATION_MINUTES,
    DURATION_MAX_MINUTES,
    DURATION_MIN_MINUTES,
    FORCED_MODE_DURATION_UNIQUE_ID_SUFFIX,
)
from .helpers import build_device_info, duration_unique_id

_DURATION_SPECS = (
    ("bypass_duration", BYPASS_DURATION_UNIQUE_ID_SUFFIX, DEFAULT_BYPASS_DURATION_MINUTES),
    (
        "forced_mode_duration",
        FORCED_MODE_DURATION_UNIQUE_ID_SUFFIX,
        DEFAULT_FORCED_MODE_DURATION_MINUTES,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the duration number entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ThreeERLConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    async_add_entities(
        ThreeERLDurationNumber(entry, translation_key, suffix, default)
        for translation_key, suffix, default in _DURATION_SPECS
    )


class ThreeERLDurationNumber(NumberEntity, RestoreEntity):
    """Duration in minutes used by the timed services as default."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = DURATION_MIN_MINUTES
    _attr_native_max_value = DURATION_MAX_MINUTES
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self, entry: ThreeERLConfigEntry, translation_key: str, suffix: str, default: float
    ) -> None:
        """Initialize the duration number.

        :param entry: Config entry.
        :type entry: ThreeERLConfigEntry
        :param translation_key: Translation key of the entity name.
        :type translation_key: str
        :param suffix: Unique id suffix.
        :type suffix: str
        :param default: Default duration in minutes.
        :type default: float
        """
        self._attr_translation_key = translation_key
        self._attr_unique_id = duration_unique_id(entry.entry_id, suffix)
        self._attr_native_value = default
        self._attr_device_info = build_device_info(entry.entry_id)

    async def async_added_to_hass(self) -> None:
        """Restore the last configured duration after a restart or reload."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            value = float(last_state.state)
        except ValueError:
            return
        if self._attr_native_min_value <= value <= self._attr_native_max_value:
            self._attr_native_value = value

    async def async_set_native_value(self, value: float) -> None:
        """Store a new duration in minutes.

        :param value: Duration in minutes.
        :type value: float
        """
        self._attr_native_value = value
        self.async_write_ha_state()
