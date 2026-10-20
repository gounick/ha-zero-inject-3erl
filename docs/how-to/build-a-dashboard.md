# Build a dashboard

Goal: add Lovelace cards for the 3ERL Zero-Injection entities.

Replace the entity IDs below with the ones generated on your Home Assistant instance. The full list is in the [entities reference](../reference/entities.md).

A ready-made view combining all these cards is available in [examples/view.yaml](../examples/view.yaml).

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
    entity: binary_sensor.3erl_zero_injection_zero_injection_active
    name: Zero-Inject actif
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

## Energy and remuneration

```yaml
type: grid
columns: 2
square: false
cards:
  - type: tile
    entity: sensor.3erl_zero_injection_curtailed_energy
    name: Énergie bridée
    icon: mdi:lightning-bolt
  - type: tile
    entity: sensor.3erl_zero_injection_cumulative_gain
    name: Gain cumulé
    icon: mdi:currency-eur
```

## History graphs

```yaml
type: history-graph
title: Bridage 3ERL — 24h
hours_to_show: 24
entities:
  - entity: binary_sensor.3erl_zero_injection_curtailment_requested
    name: Bridage demandé
  - entity: binary_sensor.3erl_zero_injection_zero_injection_active
    name: Zero-Inject actif
```

```yaml
type: history-graph
title: Gain cumulé — 7j
hours_to_show: 168
entities:
  - entity: sensor.3erl_zero_injection_cumulative_gain
    name: Gain cumulé (€)
```
