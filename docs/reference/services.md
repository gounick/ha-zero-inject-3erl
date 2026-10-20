# Services

## `zero_inject_3erl.reset_counters`

Resets the cumulative curtailed energy and `Gain cumulé` counters to zero and clears the persisted values.

Optional fields seed the counters instead of zeroing them — for example to match the totals shown on the 3ERL dashboard:

| Field | Unit | Description |
|---|---|---|
| `energy_kwh` | kWh | Starting value of the curtailed energy counter. |
| `gain_eur` | EUR | Starting value of the cumulative gain counter. |

Example call from **Developer Tools → Actions**:

```yaml
action: zero_inject_3erl.reset_counters
data:
  energy_kwh: 12.5
  gain_eur: 3.75
```
