# Entities

The integration creates the following entities per config entry. Home Assistant builds each entity ID from the device name (`3ERL Zero-Injection`) and the entity name. The table shows the IDs created on a fresh install. Renamed entities keep their custom IDs.

API and computed entities expose a translated `description` attribute under **More info → Attributes**. Supervision diagnostics expose a `reason` and the relevant relay or measurement details.

## Sensors

| Entity | Unit | Source | Description |
| --- | --- | --- | --- |
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
| `sensor.3erl_zero_injection_curtailed_energy` | kWh | computed | Cumulative estimated curtailed energy. Persisted across restarts. |

## Binary sensors

| Entity | Source | Description |
| --- | --- | --- |
| `binary_sensor.3erl_zero_injection_curtailment_requested` | `Bridage` | True when the ACI curtailment signal is active. |
| `binary_sensor.3erl_zero_injection_cdc_curtailment_requested` | `Bridage_CDC` | True when the ACC curtailment signal is active. |
| `binary_sensor.3erl_zero_injection_commanded_limitation` | computed | Limitation command after applying the selected mode; off during bypass, unknown before the first signal in Auto. Attributes: `mode`, `reason`. |
| `binary_sensor.3erl_zero_injection_relay_control_fault` | local supervision | Unavailable relays immediately, or relay disagreement lasting at least 30 seconds. Attributes: `unavailable_relays`, `misaligned_relays`, `relay_states`, `manual_bypass`, `reason`. Off during bypass. |
| `binary_sensor.3erl_zero_injection_grid_export_during_commanded_limitation` | optional grid measurement | Export above the threshold during commanded limitation after the confirmation duration. Unknown for missing, stale or invalid measurements. Attributes include source, timestamp, measured export, W/VA unit, threshold, delay and reason. No export observed does not prove effective curtailment. |
| `binary_sensor.3erl_zero_injection_3erl_data_stale` | computed | True when the latest 3ERL data is older than two publication cycles. Attribute: `data_age_minutes`. |

The commanded-limitation entity uses the unique ID suffix `commanded_limitation` and the default entity ID shown above. Legacy active-state entities are not migrated. Notifications describe the command, not relay acknowledgement or grid measurements. The original relay switches remain the source of reported relay states; no duplicate relay-state entity is created. API failures do not make local supervision or manual controls unavailable.

## Manual bypass switch

`switch.3erl_zero_injection_manual_bypass` suspends all relay commands when on, including forced On/Off modes. It does not change the physical relay state; users operate the original relay switches directly. Its value is restored after restart or reload. Turning it off immediately resumes the selected mode. This switch is independent of API availability.

## Contract visibility

ACI hides `Bridage_CDC` and current RTE PRE+. ACC hides `Bridage`, the locally estimated daily PRE+ and the 3ERL PRD3-weighted daily PRE+. These entities stay enabled and keep their history and identifiers. Contract changes update integration-managed visibility, while explicit user visibility overrides are preserved. Existing dashboard cards still show explicitly referenced hidden entities.

The estimated-remuneration entities were removed: estimated remuneration is published by 3ERL on <https://dashboard.3erl.fr> and is out of scope for this integration. No legacy entity migration or history/statistics transfer is performed. Old registry entries may remain unavailable after deployment. The stored cumulative energy total is preserved and resumed; the energy calculation still follows the API signal, not confirmed relay execution or bypass, so the counter remains an experimental estimate.

## Select

| Entity | Options | Description |
| --- | --- | --- |
| `select.3erl_zero_injection_zero_injection_mode` | `Auto`, `On`, `Off` | Operating mode. `Auto` follows the 3ERL signal, `On` and `Off` force the relay. The last value is restored after a restart. |

## Related pages

- [Configuration options](configuration-options.md)
- [3ERL API fields](api-fields.md)
