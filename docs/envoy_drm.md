# Enabling the Envoy DRM port for zero-injection

The Enphase Envoy must expose the DRM (Distributed Resource Management) port and accept the dry-contact signal from the relay. This guide explains how to enable the port and the installer-level settings.

## What is DRM?

DRM is a feature that allows an external signal to command the inverter to limit or stop grid export. In France, aggregators such as 3ERL use this mechanism to remunerate producers who temporarily stop injecting into the grid.

For Enphase systems, the DRM port is a physical terminal on the Envoy gateway. Closing the contact between the DRM terminals tells the micro-inverters to reduce production/export according to the configured DRM profile.

![DRM port identification on the Envoy-S Metered gateway](assets/electrical_wiring_diagram/identification_of_the_DRM_port_on_the_Envoy-S-Metered_gateway.png)

On the **Envoy-S Metered** gateway, the DRM port is the small terminal block above the main terminals. Look for the **Com / DRM 0** and **1 / 5** labels.

## Requirements

- An Envoy-S or IQ Gateway with a physical DRM terminal.
- A web browser.
- Access to the Envoy as **Installer**. A standard Owner account does not expose the necessary settings.

## Obtaining Installer access

By default, Enphase systems are registered under an **Owner** account. The DRM settings are only visible under an **Installer** account.

### Upgrade through the Enlighten Manager program

The simplest path for a homeowner is to use the **Enlighten Manager Upgrade Program**. You can log in with your existing Owner account.

1. Go to the [Enlighten Manager Upgrade Program](https://encare.enphase.com/?upgradeProgramType=1).
2. Choose a subscription:
   - **Monthly Subscription** — 9,99 €/month.
   - **Lifetime Subscription** — 249 € one-time.
3. Complete the purchase.
4. After confirmation, log out and log back in to Enlighten. Your account should now have **Installer** capabilities for your own system.

> This is a third-party paid service. Prices and availability depend on your region and are subject to change. This integration is not affiliated with Enphase.

### Contact Enphase support

Even after upgrading, you may find that the **Grid Profile** page is accessible but the list of available profiles is empty, or that some installer-level settings are missing for your specific system.

In that case, contact [Enphase support](https://enphase.com/fr-fr/contact-enphase-support) and ask them to grant the necessary rights for your own system. Mention that you need:

- Access to **Grid Profiles** / **Grid Management**.
- The DRM profile list to be populated so you can select the 0% export profile.

The Enphase support team can usually resolve this quickly, often by phone, and will enable the missing parameters remotely.

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
- [Enphase Envoy-S Installation and Operation Manual (PDF)](assets/enphase/EnvoySMultiphase-IOM-FR.pdf)
- [Enphase Envoy-S Quick Install Guide (PDF)](assets/enphase/Envoy-S-M-QIG-Multi-Kit-Rev05-FR-2024-01-05.pdf)
- [Enphase Envoy-S Reference Manual (PDF)](assets/enphase/Envoy-S-MAN-EN-INTL_FR.pdf)
- [Automatisation-Bridage-3ERL-Emphase](https://github.com/ALP40/Automatisation-Bridage-3ERL-Emphase)
