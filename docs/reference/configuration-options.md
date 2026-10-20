# Configuration options

All fields are set during the config flow and remain editable under **Settings → Devices & services → 3ERL Zero-Injection → Configure**.

| Field | Key | Required | Default | Description |
|---|---|---|---|---|
| 3ERL API URL | `api_url` | yes | `https://3erl.fr/api.json` | Endpoint polled for curtailment data. |
| Self-consumption contract type | `aggregation_mode` | yes | `aci` | `aci` follows the `Bridage` signal; `acc` follows `Bridage_CDC`. See [ACI vs ACC](../explanation/concepts.md#aci-vs-acc). |
| PV production power sensors | `pv_power_entity` | yes | — | One or more `sensor` entities with device class `power`, reporting production power in watts. Their values are summed, so several production sources can be combined. |
| Zero-injection relay switches | `relay_entity` | yes | — | One or more `switch` entities wired to the DRM port(s). Every listed relay is aligned with the computed state, so several production sources can be curtailed independently. |
| Home consumption power sensor | `consumption_power_entity` | no | — | `sensor` entity with device class `power`, reporting home consumption in watts. Improves the curtailed-energy estimate; see below. |
| Notification entities | `notify_service` | no | — | One or more `notify` entities that each receive a message through `notify.send_message` when the active state changes. |
| PRD3 profile day offset | `prd3_day_offset` | no | `-2` | Day offset used to pick the Enedis PRD3 profile when estimating the daily ACI price. `-2` uses the profile from two days ago because Enedis publishes yesterday's profile late in the morning. |

## Single instance

Only one config entry can be created: a household holds either an ACI or an ACC contract, never both, and the 3ERL API is a single shared endpoint — a second entry would poll the same data. Adding the integration again aborts with `already_configured`.

## Polling

There is no polling-interval option. The integration follows the update schedule published by 3ERL: it waits about 18 minutes after each `Heure_Update` and retries after about a minute when fresh data is late. See [3ERL API fields](api-fields.md#update-schedule).

## Changing options

Option changes take effect after the config entry reloads. The API URL, relay entity, power sensor, contract type, notification entity and PRD3 offset can all be updated without removing the integration. The form checks that the API answers before saving. Clear the notification field to stop notifications.
