"""Controller that applies zero-injection logic to the configured relay."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_NOTIFY_SERVICE,
    CONF_RELAY_ENTITY,
    DOMAIN,
)
from .coordinator import ThreeERLUpdateCoordinator
from .helpers import compute_zero_inject_active, get_current_mode, is_bridage_active

_LOGGER = logging.getLogger(__name__)

SELECT_MODE_UNIQUE_ID_SUFFIX = "mode"


class ZeroInjectController:
    """Applies zero-injection rules to the user relay and sends notifications.

    The controller listens to two inputs:
    - changes of the 3ERL API coordinator (bridage demand)
    - changes of the mode select entity (Auto / On / Off)

    It then decides whether the relay should be on and calls the configured
    switch service accordingly.

    :param hass: Home Assistant instance.
    :type hass: HomeAssistant
    :param entry: Config entry for this instance.
    :type entry: ConfigEntry
    :param coordinator: 3ERL data coordinator.
    :type coordinator: ThreeERLUpdateCoordinator
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: ThreeERLUpdateCoordinator,
    ) -> None:
        """Initialize the controller."""
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator
        self._relay_entity = entry.options.get(CONF_RELAY_ENTITY, entry.data[CONF_RELAY_ENTITY])
        self._notify_service = entry.options.get(
            CONF_NOTIFY_SERVICE, entry.data.get(CONF_NOTIFY_SERVICE)
        )
        self._mode_entity_id: str | None = None
        self._unsub_coordinator: Any = None
        self._unsub_mode: Any = None
        self._last_relay_state: str | None = None
        self._last_active_state: bool | None = None

    async def async_setup(self) -> None:
        """Set up listeners for coordinator and mode select updates."""
        self._mode_entity_id = self._resolve_mode_entity_id()

        self._unsub_coordinator = self._coordinator.async_add_listener(self._on_coordinator_update)

        if self._mode_entity_id:
            self._unsub_mode = async_track_state_change_event(
                self._hass,
                [self._mode_entity_id],
                self._on_mode_change,
            )

        self._apply_relay_state()

    async def async_shutdown(self) -> None:
        """Remove all listeners."""
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None
        if self._unsub_mode is not None:
            self._unsub_mode()
            self._unsub_mode = None

    @callback
    def _on_coordinator_update(self) -> None:
        """Handle a coordinator update."""
        self._apply_relay_state()

    @callback
    def _on_mode_change(self, event: Event) -> None:
        """Handle a change of the mode select entity."""
        self._apply_relay_state()

    def _resolve_mode_entity_id(self) -> str | None:
        """Find the mode select entity created by this config entry.

        :return: Entity id of the mode select, or None if not found.
        :rtype: str | None
        """
        registry = async_get_entity_registry(self._hass)
        expected_unique_id = f"{self._entry.entry_id}_{SELECT_MODE_UNIQUE_ID_SUFFIX}"
        for entity in registry.entities.values():
            if (
                entity.config_entry_id == self._entry.entry_id
                and entity.domain == "select"
                and entity.unique_id == expected_unique_id
            ):
                return entity.entity_id
        _LOGGER.warning(
            "Mode select entity not found for config entry %s",
            self._entry.entry_id,
        )
        return None

    def _compute_active_state(self) -> bool:
        """Compute whether zero-injection should be active.

        :return: True when the relay should be turned on.
        :rtype: bool
        """
        mode = get_current_mode(self._hass, self._mode_entity_id)
        bridage_active = is_bridage_active(
            self._coordinator.data.get("api_data", {}) if self._coordinator.data else {},
            self._coordinator.aggregation_mode,
        )
        return compute_zero_inject_active(mode, bridage_active)

    def _apply_relay_state(self) -> None:
        """Turn the configured relay on or off based on the computed state."""
        active = self._compute_active_state()
        if self._last_active_state == active:
            return
        self._last_active_state = active

        service = SERVICE_TURN_ON if active else SERVICE_TURN_OFF
        try:
            domain = self._relay_entity.split(".")[0]
        except (AttributeError, IndexError):
            _LOGGER.error("Invalid relay entity configured: %s", self._relay_entity)
            return

        _LOGGER.debug(
            "Applying zero-injection state: %s -> calling %s.%s on %s",
            active,
            domain,
            service,
            self._relay_entity,
        )

        self._hass.async_create_background_task(
            self._async_call_service(domain, service, {"entity_id": self._relay_entity}),
            name=f"{DOMAIN}_relay_control",
        )

        self._maybe_notify(active)

    async def _async_call_service(
        self, domain: str, service: str, service_data: dict[str, Any]
    ) -> None:
        """Call a Home Assistant service safely.

        :param domain: Service domain.
        :type domain: str
        :param service: Service name.
        :type service: str
        :param service_data: Service data.
        :type service_data: dict[str, Any]
        """
        try:
            await self._hass.services.async_call(domain, service, service_data)
        except Exception:
            _LOGGER.exception(
                "Failed to call %s.%s for relay %s",
                domain,
                service,
                self._relay_entity,
            )

    def _maybe_notify(self, active: bool) -> None:
        """Send a notification when the active state changes.

        :param active: New zero-injection active state.
        :type active: bool
        """
        if not self._notify_service:
            return

        message = (
            "3ERL zero-injection is now ACTIVE."
            if active
            else "3ERL zero-injection is now INACTIVE."
        )
        domain, service = self._notify_service.split(".", 1)

        self._hass.async_create_background_task(
            self._async_call_service(
                domain, service, {"message": message, "title": "3ERL Zero-Injection"}
            ),
            name=f"{DOMAIN}_notify",
        )
