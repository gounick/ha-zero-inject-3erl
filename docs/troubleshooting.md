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
- Check Manual bypass first. When enabled, all relay control is suspended, including forced modes. Operate the relay directly or disable bypass to resume automatic control.
- With bypass disabled, test the relay by setting the mode select to `On`. Direct toggles are corrected on a subsequent controller update.
- Check that the controller can call the service in the Home Assistant logs.
- If using a Zigbee relay, verify it is online and paired.

## Frozen or unavailable 3ERL signal

1. Enable Manual bypass. The integration stops commanding every configured relay and preserves bypass across restarts.
2. Operate the original relay switches directly and check grid export on the meter.
3. Once the source is trustworthy, select the desired mode and disable bypass. The current mode and signal take effect immediately.

Auto preserves the last known signal during API failures after a first successful response. Before any successful response it leaves relays unchanged. An unchanged flag is not necessarily a fault; check the API timestamp and data-stale diagnostic. Bypass is never enabled automatically.

## Relay control fault

Inspect `unavailable_relays`, `misaligned_relays` and `relay_states`. Unavailability is reported immediately; mismatches get a 30-second grace period. On recovery, a relay is aligned with the current command, not a queued old demand. There is no dedicated one-minute retry timer. Local supervision checks every five seconds without sending commands.

## Grid-export diagnostic is unknown

Select a positive export-only sensor in the integration options. Do not use a cumulative energy index or a signed net-power sensor. For ZLinky, check both the active-power channel in W and the apparent-power channel in VA: the latter is not an active-power measurement. Choose the channel with a reporting cadence suitable for observation, set the threshold in its W/VA base unit, and set the maximum age to match the reporting cadence.

A sample can be numerically unchanged but still need fresh reports. If HA has not received a report within the maximum age, the result is unknown. For a ZLinky `SINSTI` source that only reports on change, [examples/zlinky-sinsti-refresh.yaml](examples/zlinky-sinsti-refresh.yaml) keeps the measurement fresh by publishing a periodic `mqtt.publish` read on the device's `get` topic — every 4 minutes normally, every minute while a limitation is commanded. The diagnostic is observation only: it does not toggle relays or enable bypass. A confirmed export condition clears when export drops below the threshold, commanded limitation ends, or bypass is enabled; invalid measurements make it unknown.

## Export is not limited when relay is on

- Verify the relay limitation is configured in the Envoy installer settings.
- Confirm Level 2 sets export to **0%** (ACI) or the correct floor (ACC) when the contact is closed.
- Measure continuity across the DRM terminals when the relay is on.
- Check the wiring guide in [how-to/wire-the-relay.md](how-to/wire-the-relay.md) and the Envoy setup in [how-to/configure-envoy-drm.md](how-to/configure-envoy-drm.md).

## Missing curtailed-energy or remuneration sensors

These entities were removed intentionally. The integration cannot measure the production that would have occurred without limitation, and 3ERL already publishes estimated remuneration on <https://dashboard.3erl.fr>. Remove old dashboard, automation and script references to `sensor.3erl_zero_injection_curtailed_energy`, remuneration sensors and `zero_inject_3erl.reset_counters`.
