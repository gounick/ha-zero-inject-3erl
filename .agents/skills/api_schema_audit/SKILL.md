---
name: api_schema_audit
description: Audit the live 3ERL API schema against the integration's expectations — new or renamed fields, flag values, schedule changes — and report drift
---

Compare the live 3ERL API contract with what the integration expects. The API is public, unversioned and has no SLA; drift is the project's main external risk. Run periodically or after user reports of unknown sensors.

## 1. Fetch the live contract

- `curl -s https://3erl.fr/api.json` — capture the raw payload.
- `curl -s https://3erl.fr/api_lisezmoi.json` — the publisher's own field documentation.
- Note `Heure_Update` and `PREP_Profile` semantics from the readme payload.

## 2. Diff against the code

- Compare payload keys with `SENSOR_KEY_*` constants in `custom_components/zero_inject_3erl/const.py`.
- For each API field: is it consumed (`sensor.py`, `binary_sensor.py`, `helpers.py`), ignored on purpose, or new/unknown?
- Check `Bridage` and `Bridage_CDC` raw values against `is_flag_set` in `helpers.py` — new spellings would return None and reject the data.
- Check `Heure_Update` format against `API_TIME_FORMAT` and the publication schedule assumptions in `next_poll_delay` (≈18 min after the stamped quarter-hour).
- Check `PREP_Profile` / `PRD4` fields against `pricing.py` usage.

## 3. Report

- Table: API field → status (consumed / exposed / ignored / NEW / MISSING).
- For NEW fields: say whether they deserve an entity (see `/add_entity`) or can be ignored.
- For MISSING or renamed fields: flag as a potential bug, reference the consuming code path.
- Note the captured timestamps so the audit is reproducible.

## Rules

- Read-only audit: never edit code from this skill; propose a follow-up change instead.
- Do not hard-fail on missing fields — report the diff; some fields are conditional (e.g. `mode_degrade`, `rte_indispo_depuis`).
- One audit = one report; open an issue for actionable drift rather than fixing several things at once.
