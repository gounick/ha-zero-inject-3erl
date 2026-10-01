# Troubleshooting

## Integration does not appear in the UI

- Make sure the `custom_components/zero_inject_3erl` folder is copied under your Home Assistant `config/custom_components` directory.
- Restart Home Assistant completely (not just reload).
- Clear the browser cache or use a private window.

## Config flow fails with "cannot connect"

- Verify that your Home Assistant host can reach `https://3erl.fr/api.json`.
- Check the URL in the config flow. The default is `https://3erl.fr/api.json`.
- Look at the Home Assistant logs for the exact error.

## Relay does not turn on

- Confirm the relay switch entity ID entered in the config flow is correct.
- Test the relay manually from **Developer Tools → Services** using `switch.turn_on`.
- Check that the controller can call the service in the Home Assistant logs.
- If using a Zigbee relay, verify it is online and paired.

## Export is not limited when relay is on

- Verify the relay limitation is configured in the Envoy installer settings.
- Confirm Level 2 sets export to **0%** (ACI) or the correct floor (ACC) when the contact is closed.
- Measure continuity across the DRM terminals when the relay is on.
- Check the wiring guide in [how-to/wire-the-relay.md](how-to/wire-the-relay.md) and the Envoy setup in [how-to/configure-envoy-drm.md](how-to/configure-envoy-drm.md).

## Energy and gain counters stay at zero

- Confirm the configured PV production power sensor reports watts and updates regularly.
- Check that `binary_sensor.zero_inject_3erl_bridage_demande` is `on` during a curtailment event.
- The counters are updated every time the power sensor changes and during each API poll. They start accumulating as soon as a curtailment period begins.

## Counters look too high or too low

- The integration estimates energy as `power (W) × time (h) / 1000`. This is an approximation of the energy that would have been injected, not a measured value.
- If the PV sensor reports apparent power, production power, or a smoothed average, the estimate will be affected.
- The gain uses the latest PRE+ value from the API. The real 3ERL remuneration may use a different time-weighted price.

## Reset counters

Call the service `zero_inject_3erl.reset_counters` from **Developer Tools → Services** to reset the cumulative energy and gain counters.
