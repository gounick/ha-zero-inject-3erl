# 3ERL Zero-Injection

[![hassfest](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hassfest.yaml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hacs.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/hacs.yml)
[![Tests](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/tests.yml)
[![Security](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/security.yml)
[![Release checks](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/gounick/ha-zero-inject-3erl/actions/workflows/release.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/gounick/ha-zero-inject-3erl?style=plastic)

> **Work In Progress**: This integration is under active development. Breaking changes may occur before the first stable release.

Home Assistant custom integration that monitors the French [3ERL](https://3erl.fr) API and controls a dry-contact relay to limit photovoltaic injection when requested.

> This project is inspired by [Automatisation-Bridage-3ERL-Emphase](https://github.com/ALP40/Automatisation-Bridage-3ERL-Emphase).

## Features

- Polls the public 3ERL API (`https://3erl.fr/api.json`) for curtailment signals.
- Supports both self-consumption contract types: **ACI** (`Bridage` signal) and **ACC** (`Bridage_CDC` signal).
- Available as a HACS custom integration.
- Creates sensors for all 3ERL fields: `Bridage`, `Bridage_CDC`, `Dernier_PREP`, `PRD4`, `PREP_Profile`, `Heure_Update`, `Bridage_Long_Terme`, and more.
- Controls a Home Assistant switch/relay in three modes:
  - **Auto** — relay follows the 3ERL curtailment signal.
  - **On** — relay forced ON (zero-injection always active).
  - **Off** — relay forced OFF (zero-injection disabled).
- Tracks curtailed energy. Estimated remuneration is published by 3ERL on <https://dashboard.3erl.fr> and is intentionally not computed by the integration.
- Sends optional notifications when the limitation command changes, without claiming relay acknowledgement or zero grid export.
- Provides a persistent manual-bypass switch that releases all relay control, even during a 3ERL outage.
- Separately supervises relay acknowledgement and optional grid-export measurements, including ZLinky W or VA sensors.
- Hides contract-specific ACI/ACC entities when they do not apply, while preserving manual visibility overrides.
- Exposes a service to reset the cumulative energy counter.

## Supported PV systems

The integration currently supports a generic PV production power sensor. Auto-detection of specific inverter brands (Enphase, SMA, Fronius, etc.) may come later through provider modules; contributions for other systems are welcome.

## Requirements

- Home Assistant 2026.9.3 or newer.
- One or more switch entities controlling the zero-injection relays (e.g. a Zigbee dry-contact relay per production source).
- One or more power sensors that report current PV production in watts (their values are summed).

## Installation

### HACS (recommended)

1. Ensure that [HACS](https://hacs.xyz) is installed.
2. Add this repository as a custom repository in HACS.
3. Install **3ERL Zero-Injection**.

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=gounick&repository=ha-zero-inject-3erl&category=integration)

4. Add **3ERL Zero-Injection** to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=zero_inject_3erl)

### Manual

1. Copy the `custom_components/zero_inject_3erl` folder into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Add **3ERL Zero-Injection** to Home Assistant:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=zero_inject_3erl)

## Configuration

Follow [docs/how-to/install-and-configure.md](docs/how-to/install-and-configure.md). All fields are described in the [configuration reference](docs/reference/configuration-options.md).

One choice matters: pick **Self-consumption contract type** (`aci` or `acc`) to match your 3ERL contract. It decides which API signal drives the relay and how the Envoy relay levels must be set.

## Entities

The integration creates sensors for the 3ERL API fields, computed sensors for curtailed energy, binary sensors for the curtailment and active states, and an Auto / On / Off mode select. See the [entities reference](docs/reference/entities.md) for the full list.

## Estimated remuneration

The integration does not estimate remuneration. 3ERL publishes the estimated remuneration on its own dashboard at <https://dashboard.3erl.fr>; refer to it for settled or estimated amounts.

The cumulative curtailed-energy counter is an experimental estimate based on measured production during requested curtailment, not measured lost production. Its calculation is unchanged by manual bypass and relay diagnostics; it still follows the API signal, even if relay control is suspended.

## Development entity renames

This development version introduces new entity IDs and unique ID suffixes for commanded limitation, and removes the estimated-remuneration sensors:

- `binary_sensor.3erl_zero_injection_commanded_limitation`
- `sensor.3erl_zero_injection_estimated_cumulative_remuneration` — removed
- `sensor.3erl_zero_injection_estimated_hourly_remuneration` — removed

There is no migration or alias for the legacy entities. Update dashboard, automation and script references when deploying. Legacy registry entries may remain unavailable; old history and statistics are not automatically transferred to the new entity IDs. The `reset_counters` action now only accepts `energy_kwh`; the stored cumulative energy total is preserved.

## Manual control and supervision

Enable **Manual bypass** to suspend all relay commands, including forced On/Off modes. Operate the original relay switch directly. Bypass is restored after a restart or reload. Disabling bypass resumes the selected mode immediately and may switch the relay. A frozen signal alone does not automatically enable bypass.

**Commanded limitation** reports intent only. The relay-control fault diagnostic reports unavailable relays immediately and persistent mismatches after 30 seconds. The optional grid-export diagnostic reports export above the configured threshold during commanded limitation, after a confirmation period. No export observed is not proof of effective curtailment.

Configure a positive grid-export measurement in the integration options. ZLinky active-power measurements in W and apparent-power measurements in VA are supported as distinct quantities. The defaults are a threshold of 50 W or VA, a confirmation duration of 120 seconds, and a maximum measurement age of 300 seconds. Missing, stale, negative or non-finite measurements are unknown, never zero.

## Services

### `zero_inject_3erl.reset_counters`

Reset the cumulative curtailed energy counter to zero, or seed it with an optional `energy_kwh` value (e.g. from the 3ERL dashboard).

## Dashboard

Example Lovelace cards can be found in [docs/how-to/build-a-dashboard.md](docs/how-to/build-a-dashboard.md).

## Documentation

See [docs/README.md](docs/README.md) for the full index.

- [How 3ERL zero-injection works](docs/explanation/concepts.md)
- [Configure the Envoy DRM port](docs/how-to/configure-envoy-drm.md)
- [Wire the dry-contact relay](docs/how-to/wire-the-relay.md)
- [Install and configure](docs/how-to/install-and-configure.md)
- [Entities](docs/reference/entities.md), [configuration options](docs/reference/configuration-options.md), [API fields](docs/reference/api-fields.md), [services](docs/reference/services.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Workflow and architecture](WORKFLOW.md)

## Contributions

Contributions to support additional PV systems or other curtailment aggregators are welcome. Please open an issue before submitting a pull request.

## Development

This project uses [prek](https://prek.j178.dev/) to run linting and formatting hooks locally:

```sh
prek run --all-files
```

Tests are run with:

```sh
uv sync --extra test
uv run pytest tests/ -v
```

## License

This project is licensed under the MIT License.
