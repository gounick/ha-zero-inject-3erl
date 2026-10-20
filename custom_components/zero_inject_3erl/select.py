"""Select platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ThreeERLConfigEntry
from .const import DEFAULT_ZERO_INJECT_MODE, ZERO_INJECT_MODES
from .helpers import build_device_info, mode_unique_id

MODE_DESCRIPTION_SLUGS = {
    "Auto": "mode_auto",
    "On": "mode_on",
    "Off": "mode_off",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create select entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ThreeERLConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    async_add_entities([ThreeERLModeSelect(entry)])


class ThreeERLModeSelect(SelectEntity, RestoreEntity):
    """Select entity to control the zero-injection mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "mode"
    _attr_options = ZERO_INJECT_MODES

    def __init__(self, entry: ThreeERLConfigEntry) -> None:
        """Initialize the mode select."""
        self._attr_unique_id = mode_unique_id(entry.entry_id)
        self._attr_current_option = DEFAULT_ZERO_INJECT_MODE
        self._attr_device_info = build_device_info(entry.entry_id)

    async def async_added_to_hass(self) -> None:
        """Restore the last selected mode after a restart or reload."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ZERO_INJECT_MODES:
            self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Change the current mode.

        :param option: One of Auto, On, Off.
        :type option: str
        """
        self._attr_current_option = option
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return descriptive attributes for the current mode."""
        return {"description": MODE_DESCRIPTION_SLUGS.get(self.current_option or "", "")}
