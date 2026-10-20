# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- GitHub Actions workflows: hassfest, HACS validation, security scans, release checks.
- Security workflows: zizmor (workflow lint), CodeQL, OpenSSF Scorecard and OSV/pip-audit dependency scanning of `uv.lock`.
- README badges and improved installation instructions.
- Renovate configuration for automated dependency update pull requests, grouped weekly with a minimum release age.
- Documentation assets: wiring diagram, DRM port identification and manufacturer PDFs.
- Detailed Enphase support steps in the Envoy DRM guide.
- Self-consumption contract type option (`aci`/`acc`): selects the `Bridage` or `Bridage_CDC` API signal for the curtailment decision.
- Envoy relay-level configuration table (ACI 0% / ACC floor) in the Envoy DRM guide.
- Renamed `Curtailed energy` to `Estimated curtailed energy` to reflect that the lost surplus can only be estimated.
- Full documentation restructure following Diátaxis: explanation, how-to guides, reference and troubleshooting sections with precise Mermaid diagrams.
- Improved remuneration estimation using RTE PRE+ data and Enedis PRD3 profile, with contract-type specific logic (ACI daily average, ACC current quarter-hour).
- New sensors for current PRE+ and estimated daily PRE+.
- New sensor `Daily PRE+ weighted by PRD3 (3ERL)` exposing the `PREP_Profile_Num` API field.
- New optional `consumption_power_entity` setting: the curtailed-power estimate integrates `production − consumption` during curtailment instead of production alone, making the gain estimate reflect the surplus that would have been injected.
- Explanation of the daily PRE+ calculation, in English and French (`docs/explanation/daily-prep-estimate.md`).
- YAML package example (`docs/examples/package-3erl.yaml` and `view.yaml`) for users who prefer a pure-YAML setup.
- Entity name translations: entities use English `translation_key`s with French names in `translations/fr.json`.
- Tests for the config and options flows, setup and unload, the relay controller, sensors and binary sensors.

### Changed

- Polling now follows the schedule published by 3ERL (updates at minutes 3/18/33/48): the coordinator waits about 18 minutes after each `Heure_Update` and retries every minute when fresh data is late. The `update_interval` option was removed.
- The `pv_system_type` option was removed; it had no effect. A generic power sensor remains supported.
- The relay controller compares the computed state with the real relay state on every update. A failed call, an unavailable relay or a manual toggle is corrected on the next update. Use the mode select to force the relay.
- Notifications are sent only when the zero-injection state changes, no longer on every startup or reload.
- The mode select restores its last value after a restart or reload instead of falling back to `Auto`.
- Cumulative counters are written to disk at most once a minute and flushed on unload, instead of on every PV power change.
- `Gain cumulé` now uses the `EUR` unit and the `total` state class. Price sensors (`Dernier PRE+`, `Estimation jour PRD4`, `Current PRE+`, `Estimated daily PRE+`) no longer use the `monetary` device class. Home Assistant may ask to fix the long-term statistics unit once.
- RTE and Enedis pricing data are fetched independently, so one failing source no longer blocks the other. The daily PRD3 profile is fetched once per day.
- Entity names moved to translation keys. Fresh installs get English-based entity IDs (for example `sensor.3erl_zero_injection_estimated_curtailed_energy`); existing installs keep their current entity IDs. The mode select unique ID gains a domain prefix through a config entry migration.
- GitHub Actions are pinned by commit SHA with least-privilege `permissions` blocks, and release version strings are validated before use to prevent script injection.

### Removed

- `update_interval` and `pv_system_type` configuration fields (see Changed).
- `Estimated curtailed energy` sensor: a single power sensor cannot measure the counterfactual lost energy, and the value was misleading. The internal accumulation still feeds `Gain cumulé`.

### Fixed

- Opening the options flow crashed with `property 'config_entry' ... has no setter`.
- Reloading the entry left the old coordinator listening to the PV sensor and writing the same counters file as the new one.
- Notifications called the notify entity as a service and always failed. They now use `notify.send_message`.
- The notification service could not be cleared from the options.
- The API URL saved in the options was ignored.
- `Zero-Inject actif` did not update when the mode select changed.
- Entity IDs in the documentation did not match the IDs created by Home Assistant.
- The select unique-ID migration was never triggered because the config flow did not declare `MINOR_VERSION`.
- `Current PRE+` was permanently `unknown`: RTE publishes slots with a delay, so the current quarter-hour slot rarely exists yet. The sensor now falls back to the latest published slot.
- The Enedis PRD3 endpoint answers with a `text/html` Content-Type, so the profile fetch always failed and `Estimated daily PRE+` stayed `unknown`.

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
