"""Controller that applies zero-injection logic to the configured relay."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.notify import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_NOTIFY_SERVICE,
    CONF_RELAY_ENTITY,
    DOMAIN,
)
from .coordinator import ThreeERLUpdateCoordinator
from .helpers import (
    compute_zero_inject_active,
    entry_settings,
    get_current_mode,
    get_mode_entity_id,
)

_LOGGER = logging.getLogger(__name__)


class ZeroInjectController:
    """Applies zero-injection rules to the user relay and sends notifications.

    The controller listens to three inputs:
    - changes of the 3ERL API coordinator (bridage demand)
    - changes of the mode select entity (Auto / On / Off)
    - changes of the relay itself

    It then decides whether the relay should be on and calls the configured
    switch service when the real relay state differs.

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
        settings = entry_settings(entry)
        self._relay_entity = settings[CONF_RELAY_ENTITY]
        self._notify_service = settings.get(CONF_NOTIFY_SERVICE)
        self._mode_entity_id: str | None = None
        self._unsub_coordinator: Any = None
        self._unsub_states: Any = None
        self._last_active_state: bool | None = None

    async def async_setup(self) -> None:
        """Set up listeners for coordinator, mode select and relay updates."""
        self._mode_entity_id = self._resolve_mode_entity_id()

        self._unsub_coordinator = self._coordinator.async_add_listener(self._apply_relay_state)
        tracked = [self._relay_entity]
        if self._mode_entity_id:
            tracked.append(self._mode_entity_id)
        self._unsub_states = async_track_state_change_event(
            self._hass, tracked, self._on_state_change
        )

        self._apply_relay_state()

    async def async_shutdown(self) -> None:
        """Remove all listeners."""
        for unsub in (self._unsub_coordinator, self._unsub_states):
            if unsub is not None:
                unsub()
        self._unsub_coordinator = None
        self._unsub_states = None

    @callback
    def _on_state_change(self, event: Event) -> None:
        """Handle a change of the mode select or of the relay."""
        self._apply_relay_state()

    def _resolve_mode_entity_id(self) -> str | None:
        """Find the mode select entity created by this config entry.

        :return: Entity id of the mode select, or None if not found.
        :rtype: str | None
        """
        entity_id = get_mode_entity_id(self._hass, self._entry.entry_id)
        if entity_id is None:
            _LOGGER.warning(
                "Mode select entity not found for config entry %s",
                self._entry.entry_id,
            )
        return entity_id

    def _compute_active_state(self) -> bool:
        """Compute whether zero-injection should be active.

        :return: True when the relay should be turned on.
        :rtype: bool
        """
        mode = get_current_mode(self._hass, self._mode_entity_id)
        return compute_zero_inject_active(mode, self._coordinator.curtailment_requested)

    @callback
    def _apply_relay_state(self) -> None:
        """Align the relay with the computed state and notify on changes.

        The real relay state is compared on every call, so a failed service
        call or a manual toggle is corrected on the next update. Nothing is
        sent while the relay is unavailable; its return triggers a new call.
        """
        active = self._compute_active_state()
        if self._last_active_state is not None and self._last_active_state != active:
            self._maybe_notify(active)
        self._last_active_state = active

        relay_state = self._hass.states.get(self._relay_entity)
        if relay_state is None or relay_state.state not in (STATE_ON, STATE_OFF):
            return
        if (relay_state.state == STATE_ON) == active:
            return

        domain = self._relay_entity.split(".", 1)[0]
        service = SERVICE_TURN_ON if active else SERVICE_TURN_OFF
        _LOGGER.debug("Calling %s.%s on %s", domain, service, self._relay_entity)
        self._hass.async_create_background_task(
            self._async_call_service(domain, service, {ATTR_ENTITY_ID: self._relay_entity}),
            name=f"{DOMAIN}_relay_control",
        )

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
        except (HomeAssistantError, vol.Invalid):
            _LOGGER.exception(
                "Failed to call %s.%s on %s",
                domain,
                service,
                service_data.get(ATTR_ENTITY_ID),
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
        self._hass.async_create_background_task(
            self._async_call_service(
                NOTIFY_DOMAIN,
                SERVICE_SEND_MESSAGE,
                {
                    ATTR_ENTITY_ID: self._notify_service,
                    ATTR_MESSAGE: message,
                    ATTR_TITLE: "3ERL Zero-Injection",
                },
            ),
            name=f"{DOMAIN}_notify",
        )
