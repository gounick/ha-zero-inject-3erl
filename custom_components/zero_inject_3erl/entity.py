"""Base entity for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .helpers import build_device_info


class ThreeERLEntity(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]]):
    """Coordinator entity attached to the 3ERL Zero-Injection device.

    The unique id is built from the description key, so it stays stable
    across renames of the translated entity name.

    :param coordinator: 3ERL data coordinator.
    :type coordinator: DataUpdateCoordinator[dict[str, Any]]
    :param description: Entity description with key and translation key.
    :type description: EntityDescription
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DataUpdateCoordinator[dict[str, Any]], description: EntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry_id)
