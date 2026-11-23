---
name: ha_check
description: Verify the integration on a live Home Assistant instance via the home-assistant MCP server — deployed version, entities, services, states and log errors
---

Run after the user has deployed the integration to Home Assistant and restarted it. Use the `home-assistant` MCP tools; do not guess tool names — call `mcp_list_tools` on `home-assistant` first if unsure.

## 1. Config entry and version

- `ha_get_integration(domain="zero_inject_3erl")` — entry state must be `loaded`, `error_reason` empty.
- `ha_get_state(entity_id="update.3erl_zero_injection_update")` — `installed_version` tells which release is running. A release version (e.g. `v0.2.2`) while testing a branch means the new code is NOT deployed: report it instead of concluding the feature is broken.

## 2. Entities

- `ha_eval_template` with `{{ integration_entities('zero_inject_3erl') | list }}` — compare against `docs/reference/entities.md`. Every documented entity should exist; missing ones usually mean an old deployment or a platform that failed to set up.
- Spot-check key states with `ha_get_state`:
  - `select.3erl_zero_injection_mode_zero_inject` — `Auto`/`On`/`Off`.
  - `switch.3erl_zero_injection_bypass_manuel` — `off`/`on`.
  - `sensor.3erl_zero_injection_heure_update` — recent timestamp (`Heure_Update` tracks 15-min publication).
  - `binary_sensor.3erl_zero_injection_donnees_3erl_perimees` — `off` means fresh data.
  - `binary_sensor.3erl_zero_injection_defaut_de_pilotage_des_relais` — if `on`, read `reason`, `unavailable_relays`, `misaligned_relays` and report; a Repairs issue should also exist (Settings → Repairs).

## 3. Services

- `ha_list_services(domain="zero_inject_3erl")` — must list `set_bypass` and `set_mode` with translated names/descriptions. An empty result means the deployed code predates service registration.

## 4. Exercise new behavior (only when the user asks for a functional test)

- Press the refresh button: `ha_call_service` `button.press` on `button.3erl_zero_injection_rafraichir_les_donnees_3erl`, then confirm `sensor.3erl_zero_injection_heure_update`/`last_updated` moved.
- `zero_inject_3erl.set_mode` with a short `duration` — verify the select changes and reverts to `Auto`.
- Never touch the relay switches or forced modes without explicit user confirmation — this controls real hardware.

## 5. Logs

- `ha_get_logs(search="zero_inject", limit=50)` — check for errors, warnings or unexpected entries.

## 6. Report

Table: check → OK/FAIL → evidence. Common verdicts:

- Everything present and healthy → deployed version confirmed, feature working.
- Missing entities/services on a `v*` release version → the branch is not deployed; explain that HACS installs releases and suggest re-deploying `custom_components/` manually or releasing.
- `defaut_de_pilotage_des_relais` on → report the failing relay; this is the supervision doing its job, not necessarily an integration bug.
