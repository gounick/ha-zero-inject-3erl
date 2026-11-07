# Services

## `zero_inject_3erl.reset_counters`

Resets the cumulative curtailed energy counter to zero and clears the persisted value.

An optional field seeds the counter instead of zeroing it — for example to match the total shown on the 3ERL dashboard:

| Field | Unit | Description |
|---|---|---|
| `energy_kwh` | kWh | Starting value of the curtailed energy counter. |

Example call from **Developer Tools → Actions**:

```yaml
action: zero_inject_3erl.reset_counters
data:
  energy_kwh: 12.5
```
