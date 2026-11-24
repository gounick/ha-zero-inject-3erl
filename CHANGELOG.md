# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- New `zero_inject_3erl.set_bypass` service: enables the manual bypass, optionally for a limited `duration` in minutes after which it turns off automatically; `enable: false` disables it. Turning the bypass switch off by any means cancels a pending expiry.
- New `stale_behavior` option controlling what Auto mode does when the latest 3ERL data is older than two publication cycles: `keep_last` (default, previous behavior), `release` (relay off) or `curtail` (relay on).
- Misaligned relay commands are now retried every 30 seconds, so a relay that rejected a command or stayed misaligned without a state change is corrected without waiting for the next signal event. Each service call times out after 30 seconds instead of potentially blocking forever.
- New `test_i18n` test enforcing the bilingual documentation rules: `en.json`/`fr.json` key parity and a `*.fr.md` twin for every tracked Markdown file.
- `vulture` dead-code check in the prek hook suite, scoped to `custom_components` with a whitelist for Home Assistant lifecycle conventions.
- New `zero_inject_3erl.set_mode` service: selects the operating mode, optionally with a `duration` in minutes after which it reverts to `Auto`. Changing the mode by any other means cancels the pending revert.
- New `number` entities `bypass_duration` (default 60 min) and `forced_mode_duration` (default 30 min), persisted across restarts: `set_bypass` and `set_mode` now apply them when `duration` is omitted. Persistent bypass/mode remains available through the switch and select entities.
- New diagnostic button `button.3erl_zero_injection_refresh_3erl_data` forcing an immediate poll of the 3ERL API.
- The relay-control fault diagnostic now also raises a Repairs issue while the fault is active and clears it on recovery.
- Agent skills under `.agents/skills/`: `/add_entity`, `/pr_review`, `/release_verify`, `/bugfix` and `/api_schema_audit`.

### Changed

- The ZLinky refresh example now reads `CCAIN` (active injected power) instead of `SINSTI` and is renamed `examples/zlinky-ccain-refresh.yaml`; troubleshooting and configuration docs point to the renamed file.

## [0.2.2] - 2026-11-18

### Fixed

- Grid-export supervision: a stale measurement at zero now reports no export instead of an unknown diagnostic. Sources such as the Linky TIC production labels (ZLinky `SINSTI`/`CCAIN`) stop being republished once injection ends, which previously left the diagnostic blind with `stale_measurement`; the reason attribute still reports `stale_measurement` for transparency.
- Documentation now recommends an active-power export source in W (e.g. ZLinky `CCAIN`) over an apparent-power source in VA (e.g. ZLinky `SINSTI`), which also counts the reactive power inverters can still emit during curtailment.

## [0.2.1] - 2026-11-10

### Added

- Contribution guide (`CONTRIBUTING.md`) describing coding standards, testing and documentation requirements for contributors.
- Contributor Covenant 2.1 code of conduct.
- GitHub issue templates (bug report, feature request, question) with security reports routed to private advisories, plus a pull request template.
- OpenSSF Best Practices badge in the READMEs.
- `/release_new` agent command (`.agents/skills/`) automating the release procedure.
- PRE+ documentation gains a seasonal-trends section, the private 3ERL-RE Facebook group link and the community PRE+ history graphs.
- Secondary French `*.fr.md` versions for every Markdown file; English remains the primary documentation language.
- Local brand images under `custom_components/zero_inject_3erl/brand/` served through the Home Assistant brands API (HA 2026.3+); the READMEs display the icon.

### Changed

- Device attribution: the device manufacturer is now `gounick` and the device documentation link points to the repository — the integration is community-built, not commissioned by 3ERL.
- READMEs no longer list removed development entities that never shipped in a published release.
- Branch protection on `main`: required CI checks, no force-push, no deletion.

### Fixed

- `uv.lock` resynchronized with `pyproject.toml` (was blocking `uv sync --locked` in CI) and Pillow overridden to 13.0.0 to clear the Dependabot advisories in the test environment.

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
