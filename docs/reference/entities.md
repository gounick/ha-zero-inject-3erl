# Entities

The integration creates the following entities per config entry. Entity IDs are derived from the names below; the table shows the typical IDs.

## Sensors

| Entity | Unit | Source | Description |
|---|---|---|---|
| `sensor.zero_inject_3erl_dernier_pre` | €/MWh | `Dernier_PREP` | Latest positive imbalance settlement price. |
| `sensor.zero_inject_3erl_estimation_jour_prd4` | €/MWh | `PRD4` | Daily weighted average PREP from 3ERL. |
| `sensor.zero_inject_3erl_current_pre` | €/MWh | computed | Current quarter-hour PRE+ from RTE (used for ACC). |
| `sensor.zero_inject_3erl_estimated_daily_pre` | €/MWh | computed | Estimated daily PRE+ for ACI, computed with the Enedis PRD3 profile. |
| `sensor.zero_inject_3erl_tendance_du_jour` | — | `PREP_Profile` | Daily price trend. Attribute `heure_update` carries the API timestamp. |
| `sensor.zero_inject_3erl_heure_update` | — | `Heure_Update` | Timestamp of the last API data update. |
| `sensor.zero_inject_3erl_bridage_long_terme` | h | `Bridage_Long_Terme` | Long-term curtailment indicator. |
| `sensor.zero_inject_3erl_mode_degrade` | — | `mode_degrade` | API degraded-mode flag. |
| `sensor.zero_inject_3erl_rte_indispo_depuis` | — | `rte_indispo_depuis` | Timestamp since which RTE data is unavailable, if any. |
| `sensor.zero_inject_3erl_commentaires` | — | `Commentaires` | Operator comments published by 3ERL. |
| `sensor.zero_inject_3erl_puissance_bridable` | W | computed | Measured power during curtailment, 0 otherwise. |
| `sensor.zero_inject_3erl_puissance_gain` | €/h | computed | Current estimated remuneration rate. |
| `sensor.zero_inject_3erl_energie_bridage` | kWh | computed | Cumulative curtailed energy. Persisted across restarts. |
| `sensor.zero_inject_3erl_gain_cumule` | € | computed | Cumulative estimated gain at 70 % of PRE+. Persisted across restarts. |

## Binary sensors

| Entity | Source | Description |
|---|---|---|
| `binary_sensor.zero_inject_3erl_bridage_demande` | `Bridage` | True when the ACI curtailment signal is active. |
| `binary_sensor.zero_inject_3erl_bridage_cdc_demande` | `Bridage_CDC` | True when the ACC curtailment signal is active. |
| `binary_sensor.zero_inject_3erl_zero_inject_active` | computed | True when zero-injection is currently applied. Attributes: `mode`, `reason`. |

## Select

| Entity | Options | Description |
|---|---|---|
| `select.zero_inject_3erl_mode` | `Auto`, `On`, `Off` | Operating mode. `Auto` follows the 3ERL signal, `On` and `Off` force the relay. |

## Related pages

- [Configuration options](configuration-options.md)
- [3ERL API fields](api-fields.md)
