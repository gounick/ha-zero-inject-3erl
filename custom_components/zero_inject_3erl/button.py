"""Button platform for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ThreeERLConfigEntry
from .coordinator import ThreeERLUpdateCoordinator
from .entity import ThreeERLEntity

REFRESH_DESCRIPTION = ButtonEntityDescription(
    key="refresh",
    translation_key="refresh",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreeERLConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the refresh button for the 3ERL integration."""
    async_add_entities([ThreeERLRefreshButton(entry.runtime_data.coordinator)])


class ThreeERLRefreshButton(ThreeERLEntity, ButtonEntity):
    """Button forcing an immediate poll of the 3ERL API."""

    def __init__(self, coordinator: ThreeERLUpdateCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator, REFRESH_DESCRIPTION)

    async def async_press(self) -> None:
        """Request an immediate refresh of the 3ERL data."""
        await self.coordinator.async_request_refresh()
