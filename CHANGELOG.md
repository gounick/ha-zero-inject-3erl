# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- GitHub Actions workflows: hassfest, HACS validation, security scans, release checks.
- README badges and improved installation instructions.
- Renovate configuration for automated dependency update pull requests.
- Documentation assets: wiring diagram, DRM port identification and manufacturer PDFs.
- Detailed Enphase support steps in the Envoy DRM guide.

## [0.1.0] - 2026-09-30

### Added

- Initial release of the 3ERL Zero-Injection integration.
- Polls the public 3ERL API for curtailment signals and PREP pricing.
- Controls a configurable relay/switch for zero-injection with Auto/On/Off modes.
- Tracks curtailed PV energy and estimates 3ERL remuneration at 70% of PRE+.
- Persists cumulative energy and gain counters across restarts.
- Provides a service to reset cumulative counters.
- Supports Home Assistant config-flow setup and options flow.
- Added `helpers.py` for shared curtailment/mode decision logic.
- Added unit tests for API client, shared helpers and coordinator.
