# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-11-09

### Added

- Persistent manual-bypass switch: suspends all relay commands, including forced modes, so relays can be operated directly during frozen signals or API outages.
- Relay-control fault diagnostic with immediate unavailability reporting and a 30-second mismatch grace period, including per-relay state attributes.
- Optional grid-export supervision with configurable threshold, confirmation duration and measurement freshness. Supports W/kW and VA/kVA without treating apparent power as active power.
- Contract-aware ACI/ACC entity visibility with persistent user overrides and unchanged existing entity IDs.
- Local control and diagnostics remain loaded when the initial 3ERL request fails; Auto leaves relays unchanged until a first valid signal arrives. Options can be saved without a working API.
- Informational RTE and Enedis pricing sensors use an independent coordinator; pricing failures do not delay relay control.
- New diagnostic binary sensor `3ERL data stale`, refreshed by a local timer so its age progresses without API or sensor events.
- GitHub Actions workflows: hassfest, HACS validation, security scans and release checks.
- Documentation restructured following Diátaxis with wiring, Envoy, dashboard and troubleshooting guides.

### Changed

- Breaking development change: malformed, missing or future 3ERL signals are rejected and retried instead of being interpreted as "no curtailment". The last valid signal remains active after an earlier successful response.
- `Bridage`/`Bridage_CDC` string "1" is recognized as set; unexpected flag values become unknown rather than false.
- Polling follows the 3ERL publication schedule and bounds externally supplied timestamps, preventing a future `Heure_Update` from delaying polling for months.
- Relay commands are grouped into a single service call per domain and state, and are rechecked before a delayed service call runs.
- `relay_entity` and `notify_service` accept several entities; single-entity entries are normalized.
- Pricing computations are anchored to Europe/Paris; RTE and Enedis failures are reported independently of the control coordinator.
- Options now replace initial data as a complete set, so clearing an optional field remains cleared after saving.
- Entity names moved to translation keys; the mode select unique ID gains a domain prefix through a config-entry migration.
- The `3ERL data stale` diagnostic now reports live age and also treats a future publication timestamp as stale.

### Removed

- Breaking development change: the curtailed-energy sensor, cumulative storage, `pv_power_entity`, `consumption_power_entity` and `zero_inject_3erl.reset_counters` were removed. A power sensor cannot measure the counterfactual energy that would have been produced without limitation.
- Estimated-remuneration sensors and storage fields were removed. Remuneration is published by 3ERL on <https://dashboard.3erl.fr> and is out of scope for the integration.
- `puissance_bridable`, `update_interval` and `pv_system_type` fields and entities were removed.
- Legacy entity migration, aliases and statistics transfer are not provided for removed development entities; old registry entries may remain unavailable.

### Fixed

- Opening the options flow no longer crashes or resurrects an optional field removed in a previous save.
- Notifications use `notify.send_message` and are sent only on command transitions.
- `Current PRE+` falls back to the latest published quarter-hour slot instead of staying unknown.
- Invalid or non-finite RTE/Enedis payload values are ignored instead of propagating `NaN` or infinity into price sensors.
- The Enedis PRD3 `text/html` JSON response is parsed correctly.
- Unloading while pricing is blocked cancels the background refresh without failing the entry unload.
- Documentation no longer promises a hardware fail-open behavior that the software cannot guarantee.

## [0.1.0] - 2026-09-30

### Added in 0.1.0

- Initial release of the 3ERL Zero-Injection integration.
- Polls the public 3ERL API for curtailment signals and PREP pricing.
- Controls a configurable relay/switch for zero-injection with Auto/On/Off modes.
- Tracks curtailed PV energy and estimates 3ERL remuneration at 70% of PRE+.
- Persists cumulative energy and gain counters across restarts.
- Provides a service to reset cumulative counters.
- Supports Home Assistant config-flow setup and options flow.
- Added `helpers.py` for shared curtailment/mode decision logic.
- Added unit tests for API client, shared helpers and coordinator.
