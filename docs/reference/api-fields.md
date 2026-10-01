# 3ERL API fields

The integration polls `https://3erl.fr/api.json` and exposes the following fields.

| Field | Type | Used for |
|---|---|---|
| `Bridage` | 0 / 1 | ACI curtailment signal. Drives the relay when the contract type is `aci`. |
| `Bridage_CDC` | 0 / 1 | ACC curtailment signal. Drives the relay when the contract type is `acc`. |
| `Dernier_PREP` | €/MWh | Latest positive imbalance settlement price (PRE+). Used in the gain estimate. |
| `PRD4` | €/MWh | Daily weighted average PREP. In ACI, this is the price applied to injected surplus. |
| `PREP_Profile` | string | Daily price trend indicator. |
| `Heure_Update` | string | Timestamp of the last API update. |
| `Bridage_Long_Terme` | number | Long-term curtailment indicator. |
| `mode_degrade` | — | Degraded-mode flag published by 3ERL. |
| `rte_indispo_depuis` | string | Timestamp since which RTE data is unavailable, if any. |
| `Commentaires` | string | Operator comments. |

The API refreshes every 15 minutes. The default polling interval matches this cadence.
