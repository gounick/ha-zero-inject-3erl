# Build a dashboard

Goal: add Lovelace cards for the 3ERL Zero-Injection entities.

Replace the entity IDs below with the ones generated on your Home Assistant instance. The full list is in the [entities reference](../reference/entities.md).

A ready-made view combining all these cards is available in [examples/view.yaml](../examples/view.yaml).

This development version introduces the new commanded-limitation entity ID and removes the estimated-remuneration and curtailed-energy sensors without legacy migration. Update existing cards, automations and scripts to the IDs shown here. Estimated remuneration is published by 3ERL on <https://dashboard.3erl.fr>. Contract-specific hiding does not remove explicit references from cards. Use the ACI demand and daily PRE+ for ACI, or the CDC demand and current PRE+ for ACC.

## Compare command, relay and observed export

Add these tiles alongside the mode and demand:

```yaml
type: entities
entities:
  - switch.3erl_zero_injection_manual_bypass
  - binary_sensor.3erl_zero_injection_commanded_limitation
  - switch.your_relay_switch
  - binary_sensor.3erl_zero_injection_relay_control_fault
  - binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation
```

Replace `switch.your_relay_switch` with the original relay switch. Enable bypass before operating it directly. Configure the grid-export source in the integration options; unknown means there is no trustworthy recent measurement. Neither a reported relay ON nor no export observed proves effective curtailment.

## Overview tiles

```yaml
type: grid
columns: 3
square: false
cards:
  - type: tile
    entity: select.3erl_zero_injection_zero_injection_mode
    name: Mode zero-inject
    icon: mdi:tune
  - type: tile
    entity: binary_sensor.3erl_zero_injection_curtailment_requested
    name: Bridage demandé
    icon: mdi:car-speed-limiter
  - type: tile
    entity: binary_sensor.3erl_zero_injection_commanded_limitation
    name: Commanded limitation
    icon: mdi:flash-off
```

## Pricing and trend

```yaml
type: grid
columns: 3
square: false
cards:
  - type: tile
    entity: sensor.3erl_zero_injection_latest_pre
    name: Dernier PRE+
    icon: mdi:currency-eur
  - type: tile
    entity: sensor.3erl_zero_injection_daily_pre_average_prd4
    name: PRD4
    icon: mdi:chart-line
  - type: tile
    entity: sensor.3erl_zero_injection_daily_trend
    name: Tendance
    icon: mdi:trending-up
```

## Diagnostics

```yaml
type: grid
columns: 2
square: false
cards:
  - type: tile
    entity: binary_sensor.3erl_zero_injection_3erl_data_stale
    name: Data freshness
    icon: mdi:cloud-alert-outline
  - type: tile
    entity: binary_sensor.3erl_zero_injection_relay_control_fault
    name: Relay control fault
    icon: mdi:alert-outline
```

## History graphs

```yaml
type: history-graph
title: Bridage 3ERL — 24h
hours_to_show: 24
entities:
  - entity: binary_sensor.3erl_zero_injection_curtailment_requested
    name: Bridage demandé
  - entity: binary_sensor.3erl_zero_injection_commanded_limitation
    name: Commanded limitation
```

```yaml
type: history-graph
title: Diagnostics — 24h
hours_to_show: 24
entities:
  - entity: binary_sensor.3erl_zero_injection_3erl_data_stale
    name: Stale API data
  - entity: binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation
    name: Observed export
```
