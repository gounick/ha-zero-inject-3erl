"""Select platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_ZERO_INJECT_MODE, DOMAIN, ZERO_INJECT_MODES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create select entities for the 3ERL integration.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry being set up.
    :type entry: ConfigEntry
    :param async_add_entities: Callback to register entities.
    :type async_add_entities: AddEntitiesCallback
    """
    async_add_entities([ThreeERLModeSelect(entry)])


class ThreeERLModeSelect(SelectEntity):
    """Select entity to control the zero-injection mode."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:tune"
    _attr_options = ZERO_INJECT_MODES

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the mode select."""
        self._entry = entry
        self._attr_name = "Mode zero-inject"
        self._attr_unique_id = f"{entry.entry_id}_mode"
        self._attr_current_option = DEFAULT_ZERO_INJECT_MODE
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="3ERL Zero-Injection",
            manufacturer="3ERL",
            model="Zero-Injection",
            configuration_url="https://3erl.fr",
        )

    async def async_select_option(self, option: str) -> None:
        """Change the current mode.

        :param option: One of Auto, On, Off.
        :type option: str
        """
        if option not in ZERO_INJECT_MODES:
            raise ValueError(f"Invalid mode: {option}")
        self._attr_current_option = option
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return descriptive attributes for the current mode."""
        descriptions = {
            "Auto": "Relay follows the 3ERL curtailment signal.",
            "On": "Relay forced ON (zero-injection always active).",
            "Off": "Relay forced OFF (zero-injection disabled).",
        }
        return {"description": descriptions.get(self.current_option, "")}
