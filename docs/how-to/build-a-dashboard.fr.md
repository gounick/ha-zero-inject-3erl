# Construire un tableau de bord

Objectif : ajouter des cartes Lovelace pour les entités 3ERL Zero-Injection.

Remplacez les ID ci-dessous par ceux générés sur votre instance. La liste complète figure dans la [référence des entités](../reference/entities.fr.md).

Une vue prête à l’emploi combinant ces cartes est disponible dans [examples/view.yaml](../examples/view.yaml).

Cette version de développement introduit la nouvelle entité `commanded_limitation` et supprime sans migration les capteurs de rémunération estimée et d’énergie bridée. Mettez à jour les cartes, automatisations et scripts avec les ID indiqués ici. La rémunération estimée est publiée par 3ERL sur <https://dashboard.3erl.fr>. Le masquage propre au contrat ne retire pas les références explicites des cartes. Utilisez la demande ACI et le PRE+ journalier pour l’ACI, ou la demande CDC et le PRE+ courant pour l’ACC.

## Comparer commande, relais et export observé

Ajoutez ces tuiles à côté du mode et de la demande :

```yaml
type: entities
entities:
  - switch.3erl_zero_injection_manual_bypass
  - binary_sensor.3erl_zero_injection_commanded_limitation
  - switch.your_relay_switch
  - binary_sensor.3erl_zero_injection_relay_control_fault
  - binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation
```

Remplacez `switch.your_relay_switch` par le switch du relais d’origine. Activez le bypass avant de le piloter directement. Configurez la source d’export dans les options ; `unknown` signifie qu’aucune mesure récente fiable n’existe. Un relais déclaré ON, comme une absence d’export observée, ne prouve pas que le bridage est effectif.

## Tuiles de vue d’ensemble

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
    name: Limitation commandée
    icon: mdi:flash-off
```

## Prix et tendance

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
    name: Fraîcheur des données
    icon: mdi:cloud-alert-outline
  - type: tile
    entity: binary_sensor.3erl_zero_injection_relay_control_fault
    name: Défaut relais
    icon: mdi:alert-outline
```

## Graphes d’historique

```yaml
type: history-graph
title: Bridage 3ERL — 24 h
hours_to_show: 24
entities:
  - entity: binary_sensor.3erl_zero_injection_curtailment_requested
    name: Bridage demandé
  - entity: binary_sensor.3erl_zero_injection_commanded_limitation
    name: Limitation commandée
```

```yaml
type: history-graph
title: Diagnostics — 24 h
hours_to_show: 24
entities:
  - entity: binary_sensor.3erl_zero_injection_3erl_data_stale
    name: Données API périmées
  - entity: binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation
    name: Export observé
```
