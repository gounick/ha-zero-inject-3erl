# Entities

The integration creates the following entities per config entry. Home Assistant builds each entity ID from the device name (`3ERL Zero-Injection`) and the entity name. The table shows the IDs created on a fresh install. Renamed entities keep their custom IDs.

## Sensors

| Entity | Unit | Source | Description |
|---|---|---|---|
| `sensor.3erl_zero_injection_latest_pre` | €/MWh | `Dernier_PREP` | Latest positive imbalance settlement price. |
| `sensor.3erl_zero_injection_daily_pre_average_prd4` | €/MWh | `PRD4` | Daily weighted average PRE+ as published by 3ERL. |
| `sensor.3erl_zero_injection_daily_pre_weighted_by_prd3_3erl` | €/MWh | `PREP_Profile_Num` | Daily PRE+ weighted by the PRD3 profile, computed by 3ERL. |
| `sensor.3erl_zero_injection_current_pre` | €/MWh | computed | Current quarter-hour PRE+ from RTE (used for ACC). |
| `sensor.3erl_zero_injection_estimated_daily_pre` | €/MWh | computed | Estimated daily PRE+ for ACI, computed with the Enedis PRD3 profile. |
| `sensor.3erl_zero_injection_daily_trend` | — | `PREP_Profile` | Daily price trend. Attribute `heure_update` carries the API timestamp. |
| `sensor.3erl_zero_injection_last_rte_update` | — | `Heure_Update` | Timestamp of the last API data update. |
| `sensor.3erl_zero_injection_long_term_curtailment_until` | — | `Bridage_Long_Terme` | Long-term curtailment indicator. |
| `sensor.3erl_zero_injection_degraded_mode` | — | `mode_degrade` | API degraded-mode flag. |
| `sensor.3erl_zero_injection_rte_unavailable_since` | — | `rte_indispo_depuis` | Timestamp since which RTE data is unavailable, if any. |
| `sensor.3erl_zero_injection_comments` | — | `Commentaires` | Operator comments published by 3ERL. |
| `sensor.3erl_zero_injection_curtailable_power` | W | computed | Measured power during curtailment, 0 otherwise. |
| `sensor.3erl_zero_injection_gain_rate` | €/h | computed | Current estimated remuneration rate. |
| `sensor.3erl_zero_injection_estimated_curtailed_energy` | kWh | computed | Estimated energy not injected because of curtailment. Persisted across restarts. |
| `sensor.3erl_zero_injection_cumulative_gain` | EUR | computed | Cumulative estimated gain at 70 % of PRE+. Persisted across restarts. |

## Binary sensors

| Entity | Source | Description |
|---|---|---|
| `binary_sensor.3erl_zero_injection_curtailment_requested` | `Bridage` | True when the ACI curtailment signal is active. |
| `binary_sensor.3erl_zero_injection_cdc_curtailment_requested` | `Bridage_CDC` | True when the ACC curtailment signal is active. |
| `binary_sensor.3erl_zero_injection_zero_injection_active` | computed | True when zero-injection is currently applied. Attributes: `mode`, `reason`. |

## Select

| Entity | Options | Description |
|---|---|---|
| `select.3erl_zero_injection_zero_injection_mode` | `Auto`, `On`, `Off` | Operating mode. `Auto` follows the 3ERL signal, `On` and `Off` force the relay. The last value is restored after a restart. |

## Related pages

- [Configuration options](configuration-options.md)
- [3ERL API fields](api-fields.md)
