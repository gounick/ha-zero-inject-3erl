# 3ERL API fields

The integration polls `https://3erl.fr/api.json` and exposes the following fields.

| Field | Type | Used for |
|---|---|---|
| `Bridage` | 0 / 1 | ACI curtailment signal. Drives the relay when the contract type is `aci`. |
| `Bridage_CDC` | 0 / 1 | ACC curtailment signal. Drives the relay when the contract type is `acc`. |
| `Dernier_PREP` | €/MWh | Latest positive imbalance settlement price (PRE+). Fallback in the gain estimate when the RTE/Enedis sources are unavailable. |
| `PRD4` | €/MWh | Daily weighted average PRE+ as published by 3ERL. In ACI, this is the price applied to injected surplus. See [How the daily PRE+ is calculated](../explanation/daily-prep-estimate.md). |
| `PREP_Profile` | string | Daily price trend indicator. |
| `PREP_Profile_Num` | €/MWh | Numeric form of the daily price trend. |
| `Heure_Update` | string | Timestamp of the last API update. |
| `Bridage_Long_Terme` | number | Long-term curtailment indicator. |
| `mode_degrade` | — | Degraded-mode flag published by 3ERL. |
| `rte_indispo_depuis` | string | Timestamp since which RTE data is unavailable, if any. |
| `Commentaires` | string | Operator comments. |

## Update schedule

According to 3ERL, the API data is refreshed at minutes 3, 18, 33 and 48 of each hour, plus a few seconds. When 3ERL could not get the RTE data on time, it retries every minute until the data arrives.

The integration follows that schedule: after each successful poll it reads `Heure_Update` and waits about 18 minutes before polling again. When the update timestamp is missing, malformed or older than expected, it retries after about a minute. Polling more often would not return fresher data.
