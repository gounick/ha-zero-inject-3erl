# Enabling the Envoy DRM port for zero-injection

The Enphase Envoy must expose the DRM (Distributed Resource Management) port and accept the dry-contact signal from the relay. This guide explains how to enable the port and the installer-level settings.

## What is DRM?

DRM is a feature that allows an external signal to command the inverter to limit or stop grid export. In France, aggregators such as 3ERL use this mechanism to remunerate producers who temporarily stop injecting into the grid.

For Enphase systems, the DRM port is a physical terminal on the Envoy gateway. Closing the contact between the DRM terminals tells the micro-inverters to reduce production/export according to the configured DRM profile.

## Requirements

- An Envoy-S or IQ Gateway with a physical DRM terminal.
- A web browser.
- Access to the Envoy as **Installer**. A standard Owner account does not expose the necessary settings.

## Obtaining Installer access

By default, Enphase systems are registered under an **Owner** account. The DRM settings are only visible under an **Installer** account.

### Option 1: Convert your account through Enlighten

1. Log in to [Enphase Enlighten](https://enlighten.enphaseenergy.com).
2. Open the system and go to **Settings → Access**.
3. Request to change your role to **Installer**. Depending on your region, this may require support from the original installer or Enphase.

### Option 2: Use the installer toolkit (legacy)

Some older firmware versions allow local access via the Envoy installer toolkit app. This method is being phased out and may not work on recent firmware.

### Option 3: Lifetime Installer subscription

Enphase offers a paid **Lifetime** subscription that converts a homeowner account to full Installer access for a single system. This is a one-time purchase managed through the Enlighten portal.

Steps:

1. Log in to [Enphase Enlighten](https://enlighten.enphaseenergy.com).
2. Navigate to the **Subscriptions** or **Installer access** section.
3. Purchase the **Lifetime** subscription for the system you want to control.
4. After confirmation, log out and log back in. The system should now show **Installer** role.

> This is a third-party paid service. Prices and availability depend on your region and are subject to change. This integration is not affiliated with Enphase.

## Enabling the DRM port

Once you have Installer access:

1. Open a web browser and go to the Envoy local IP address.
2. Log in with your Enlighten credentials.
3. Navigate to **Installer → Settings → Grid Profiles** or **Grid Management**.
4. Enable the **DRM** port if it is disabled.
5. Select the appropriate DRM profile. For 3ERL zero-injection, choose a profile that sets export to **0%** when the DRM contact is closed.
6. Save the settings and wait for the micro-inverters to apply the new profile (this can take a few minutes).

## Verifying DRM behavior

1. Go to the Envoy web interface and check the live production/export values.
2. Manually turn on the relay from Home Assistant.
3. The Envoy should report near-zero or zero export within a few seconds.
4. Turn the relay off. Export should resume after a short delay.

If the export does not drop to zero when the DRM contact is closed, verify:

- The DRM profile is correctly selected.
- The relay wiring uses the dry-contact output only.
- The relay contact is actually closing (measure continuity with a multimeter).
- The Envoy firmware supports DRM on your model.

## Troubleshooting

| Symptom | Possible cause | Action |
|---------|----------------|--------|
| No DRM terminal visible | Envoy model lacks DRM port | Check the datasheet; consider an external zero-export device. |
| DRM settings grayed out | Logged in as Owner, not Installer | Convert account or use Installer credentials. |
| Relay closes but export stays high | Wrong DRM profile selected | Choose a 0% export profile. |
| Micro-inverters take minutes to react | Firmware update in progress | Wait and retry. |

## References

- [Enphase Enlighten](https://enlighten.enphaseenergy.com)
- Enphase Envoy and IQ Gateway installation manuals
- [Automatisation-Bridage-3ERL-Emphase](https://github.com/ALP40/Automatisation-Bridage-3ERL-Emphase)
