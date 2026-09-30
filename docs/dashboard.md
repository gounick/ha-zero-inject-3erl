# Dashboard examples

This page provides example Lovelace cards for the 3ERL Zero-Injection integration.

Replace the entity IDs below with the ones generated on your Home Assistant instance.

## Overview tiles

```yaml
type: grid
columns: 3
square: false
cards:
  - type: tile
    entity: input_select.zero_inject_3erl_mode_zero_inject
    name: Mode zero-inject
    icon: mdi:tune
  - type: tile
    entity: binary_sensor.zero_inject_3erl_bridage_demande
    name: Bridage demandé
    icon: mdi:car-speed-limiter
  - type: tile
    entity: binary_sensor.zero_inject_3erl_zero_inject_active
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
    entity: sensor.zero_inject_3erl_dernier_pre
    name: Dernier PRE+
    icon: mdi:currency-eur
  - type: tile
    entity: sensor.zero_inject_3erl_prd4
    name: PRD4
    icon: mdi:chart-line
  - type: tile
    entity: sensor.zero_inject_3erl_tendance_du_jour
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
    entity: sensor.zero_inject_3erl_energie_bridage
    name: Énergie bridage
    icon: mdi:counter
  - type: tile
    entity: sensor.zero_inject_3erl_gain_cumule
    name: Gain cumulé
    icon: mdi:currency-eur
```

## History graphs

```yaml
type: history-graph
title: Bridage 3ERL — 24h
hours_to_show: 24
entities:
  - entity: binary_sensor.zero_inject_3erl_bridage_demande
    name: Bridage demandé
  - entity: binary_sensor.zero_inject_3erl_zero_inject_active
    name: Zero-Inject actif
```

```yaml
type: history-graph
title: Énergie bridée & gain cumulé — 7j
hours_to_show: 168
entities:
  - entity: sensor.zero_inject_3erl_energie_bridage
    name: Énergie bridée (kWh)
  - entity: sensor.zero_inject_3erl_gain_cumule
    name: Gain cumulé (€)
```
