# Configuration options

All fields are set during the config flow and remain editable under **Settings → Devices & services → 3ERL Zero-Injection → Configure**.

| Field | Key | Required | Default | Description |
|---|---|---|---|---|
| 3ERL API URL | `api_url` | yes | `https://3erl.fr/api.json` | Endpoint polled for curtailment data. |
| Update interval | `update_interval` | yes | `15` | Polling interval in minutes (1–60). The API refreshes every 15 minutes. |
| PV system type | `pv_system_type` | yes | `generic` | Reserved for future auto-detection. Choose `generic`. |
| Self-consumption contract type | `aggregation_mode` | yes | `aci` | `aci` follows the `Bridage` signal; `acc` follows `Bridage_CDC`. See [ACI vs ACC](../explanation/concepts.md#aci-vs-acc). |
| PV production power sensor | `pv_power_entity` | yes | — | `sensor` entity with device class `power`, reporting injected power in watts. |
| Zero-injection relay switch | `relay_entity` | yes | — | `switch` entity wired to the DRM port. |
| Notification service | `notify_service` | no | — | `notify` entity called on active-state changes. |

## Changing options

Option changes take effect after the config entry reloads. The relay entity, power sensor, contract type, interval and notification service can all be updated without removing the integration.
