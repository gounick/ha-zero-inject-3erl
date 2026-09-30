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
- Creates sensors for all 3ERL fields: `Bridage`, `Bridage_CDC`, `Dernier_PREP`, `PRD4`, `PREP_Profile`, `Heure_Update`, `Bridage_Long_Terme`, and more.
- Controls a Home Assistant switch/relay in three modes:
  - **Auto** — relay follows the 3ERL curtailment signal.
  - **On** — relay forced ON (zero-injection always active).
  - **Off** — relay forced OFF (zero-injection disabled).
- Tracks curtailed energy and estimates 3ERL remuneration (70% of PRE+).
- Sends optional notifications when the active state changes.
- Exposes a service to reset cumulative energy and gain counters.

## Supported PV systems

The integration currently supports a generic PV production power sensor. The `PV system type` field is reserved for future auto-discovery of specific inverter brands (Enphase, SMA, Fronius, etc.). Contributions for other systems are welcome.

## Requirements

- Home Assistant 2026.9.3 or newer.
- A switch entity that controls the zero-injection relay (e.g. a Zigbee dry-contact relay).
- A power sensor that reports current PV production in watts.

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

1. Go to **Settings** → **Devices & services**.
2. Click **Add integration** and search for **3ERL Zero-Injection**.
3. Configure:
   - **3ERL API URL** — leave the default unless you use a mirror.
   - **Update interval** — how often to poll the 3ERL API (default: 15 minutes).
   - **PV system type** — reserved for future use; choose **Generic**.
   - **PV production power sensor** — a power sensor reporting current PV production in watts.
   - **Zero-injection relay switch** — the switch that controls the relay wired to your inverter DRM port.
   - **Notification service** — optional `notify.*` service for state-change notifications.

## Entities

The integration creates the following entities per config entry:

| Entity | Type | Description |
|---|---|---|
| `sensor.zero_inject_3erl_dernier_pre` | Sensor | Latest PRE+ value (€/MWh). |
| `sensor.zero_inject_3erl_prd4` | Sensor | Daily average PREP value (€/MWh). |
| `sensor.zero_inject_3erl_tendance_du_jour` | Sensor | Current PREP profile trend. |
| `sensor.zero_inject_3erl_puissance_bridable` | Sensor | PV power during curtailment periods (W). |
| `sensor.zero_inject_3erl_puissance_gain` | Sensor | Estimated current remuneration rate (€/h). |
| `sensor.zero_inject_3erl_energie_bridage` | Sensor | Cumulative curtailed energy (kWh). |
| `sensor.zero_inject_3erl_gain_cumule` | Sensor | Cumulative estimated gain (€). |
| `binary_sensor.zero_inject_3erl_bridage_demande` | Binary sensor | True when 3ERL requests curtailment. |
| `binary_sensor.zero_inject_3erl_bridage_cdc_demande` | Binary sensor | True when 3ERL requests CDC curtailment. |
| `binary_sensor.zero_inject_3erl_zero_inject_active` | Binary sensor | True when zero-injection is currently active. |
| `select.zero_inject_3erl_mode_zero_inject` | Select | Auto / On / Off mode. |

## How remuneration is estimated

3ERL remunerates participants with 70% of the positive imbalance settlement price (PRE+) when market prices are positive. The integration computes:

```text
gain (€) = energy_bridée (kWh) × Dernier_PREP (€/MWh) × 0.7 / 1000
```

The cumulative values are persisted across Home Assistant restarts.

## Services

### `zero_inject_3erl.reset_counters`

Reset the cumulative `Énergie bridage` and `Gain cumulé` sensors to zero.

## Dashboard

Example Lovelace cards can be found in [docs/dashboard.md](docs/dashboard.md).

## Documentation

- [Wiring the dry-contact relay](docs/wiring.md)
- [Enabling Envoy DRM port](docs/envoy_drm.md)
- [Dashboard examples](docs/dashboard.md)
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
