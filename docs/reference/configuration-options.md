# Configuration options

All fields are set during the config flow and remain editable under **Settings → Devices & services → 3ERL Zero-Injection → Configure**.

| Field | Key | Required | Default | Description |
|---|---|---|---|---|
| 3ERL API URL | `api_url` | yes | `https://3erl.fr/api.json` | Endpoint polled for curtailment data. |
| Self-consumption contract type | `aggregation_mode` | yes | `aci` | `aci` follows the `Bridage` signal; `acc` follows `Bridage_CDC`. See [ACI vs ACC](../explanation/concepts.md#aci-vs-acc). |
| PV production power sensors | `pv_power_entity` | yes | — | One or more `sensor` entities with device class `power`, reporting production power in watts. Their values are summed, so several production sources can be combined. |
| Zero-injection relay switches | `relay_entity` | yes | — | One or more `switch` entities wired to the DRM port(s). Every listed relay is aligned with the computed state, so several production sources can be curtailed independently. |
| Home consumption power sensor | `consumption_power_entity` | no | — | `sensor` entity with device class `power`, reporting home consumption in watts. Improves the curtailed-energy estimate; see below. |
| Grid export sensor | `injection_power_entity` | no | — | Positive export-only measurement at the grid connection, in W/kW or VA/kVA. Signed net-power and energy counters are not supported. Only used for observation, never for relay control. |
| Export threshold | `injection_threshold` | no | `50` | Threshold in W for active-power sources or VA for apparent-power sources, after k-unit scaling. Range 0–10000. |
| Export confirmation duration | `injection_delay` | no | `120` | Seconds continuously above the threshold during commanded limitation before the export diagnostic turns on. Range 1–3600. |
| Maximum export measurement age | `injection_max_age` | no | `300` | Seconds since HA last received a report from the source. Older, missing or invalid measurements produce an unknown diagnostic, not a no-export result. Range 1–3600. |
| Notification entities | `notify_service` | no | — | One or more `notify` entities that each receive a message through `notify.send_message` when the active state changes. |
| PRD3 profile day offset | `prd3_day_offset` | no | `-2` | Day offset used to pick the Enedis PRD3 profile when estimating the daily ACI price. `-2` uses the profile from two days ago because Enedis publishes yesterday's profile late in the morning. |

## Single instance

Only one config entry can be created: a household holds either an ACI or an ACC contract, never both, and the 3ERL API is a single shared endpoint — a second entry would poll the same data. Adding the integration again aborts with `already_configured`.

## Polling

There is no polling-interval option. The integration follows the update schedule published by 3ERL: it waits about 18 minutes after each `Heure_Update` and retries after about a minute when fresh data is late. See [3ERL API fields](api-fields.md#update-schedule).

## Changing options

Option changes take effect after the config entry reloads. The API URL, relay entity, power sensor, contract type, notification entity and PRD3 offset can all be updated without removing the integration. Initial installation checks the API, but the options form does not require it to be reachable. Local control remains available during outages. Clear the notification field to stop notifications, or the grid export field to stop export observation. A measurement source must report often enough for the configured maximum age; an unchanged number is not evidence of a fresh report.
