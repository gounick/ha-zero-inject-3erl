# Services

## `zero_inject_3erl.set_bypass`

Turns the manual bypass on or off, optionally for a limited duration.

| Field | Required | Description |
|---|---|---|
| `enable` | no | `true` (default) turns the bypass on; `false` turns it off and cancels any pending expiry. |
| `duration` | no | Duration in minutes (1–1440) after which the bypass turns off automatically. Omit to use the configured **Bypass duration** number. |

The bypass is always timed through this service; for a persistent bypass, use the `switch.3erl_zero_injection_manual_bypass` entity instead.

Turning the bypass switch off directly — or calling `set_bypass` with `enable: false` — cancels a pending expiry. Disabling the bypass resumes the selected mode and may switch the relay immediately.

## `zero_inject_3erl.set_mode`

Selects the zero-injection mode, optionally for a limited duration.

| Field | Required | Description |
|---|---|---|
| `mode` | yes | One of `Auto`, `On`, `Off`. |
| `duration` | no | Duration in minutes (1–1440) after which the mode reverts to `Auto`. Omit to use the configured **Forced mode duration** number. |

Mode selection through this service is always timed; for a persistent selection, use the mode select entity instead.

Changing the mode by any other means (select entity, another `set_mode` call) cancels a pending revert.

User control is also exposed through entities:

- `select.3erl_zero_injection_zero_injection_mode` for Auto / On / Off.
- `switch.3erl_zero_injection_manual_bypass` to suspend all relay commands.

Estimated remuneration and curtailed energy are out of scope. See the [entities reference](entities.md).
