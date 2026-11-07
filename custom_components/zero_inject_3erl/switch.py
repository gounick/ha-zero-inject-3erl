from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ThreeERLConfigEntry
from .const import DOMAIN
from .helpers import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ThreeERLBypassSwitch(entry)])


class ThreeERLBypassSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "manual_bypass"
    _attr_icon = "mdi:hand-back-right"
    _attr_is_on = False

    def __init__(self, entry: ThreeERLConfigEntry) -> None:
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_manual_bypass"
        self._attr_device_info = build_device_info(entry.entry_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
