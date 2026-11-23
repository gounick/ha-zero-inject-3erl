---
name: add_entity
description: Scaffold a new sensor, binary_sensor or other entity end to end — platform code, unique id, icons, translations, visibility, tests, docs and changelog
---

Add a new entity to the `zero_inject_3erl` integration without missing a file. Adding an entity touches many places; follow this checklist in order and verify each item before moving on.

## 1. Understand the data source

- API-driven entity: value comes from `coordinator.data["api_data"]` or a computed key on `ThreeERLUpdateCoordinator`.
- Price-driven entity: value comes from `pricing_coordinator` (`current_prep`, `estimated_daily_prep`, …).
- Locally computed entity (supervision, commanded state): lives in `binary_sensor.py`/`supervision.py` and reads entities and controller state, never the API directly.

`sensor.py` and `binary_sensor.py` must never call the API; they read `coordinator.data`.

## 2. Add the entity

- API flag → reuse `ThreeERLApiBinarySensor` with a new description in `API_FLAGS` (binary_sensor.py).
- API text/diagnostic → add a `_text(...)` entry in `SENSORS` (sensor.py).
- Price → add a `_price(...)` entry in `SENSORS`, attached to `pricing_coordinator` (extend the coordinator list in `async_setup_entry` if needed).
- Computed → dedicated class following `ThreeERLCommandedLimitationBinarySensor` or `ThreeERLSupervisionSensor`.
- Unique id is built from `EntityDescription.key` — choose a stable snake_case key; it is the `translation_key` too.
- API field constants go in `const.py` as `SENSOR_KEY_*`.

## 3. Register the surroundings

- `icons.json`: add an icon under `entity.<domain>.<key>`.
- `translations/en.json` and `translations/fr.json`: add the entity name (and attribute states) under `entity.<domain>.<key>`. Both files must stay in sync — `tests/test_i18n.py` enforces key parity.
- `visibility.py`: if the entity only applies to one contract (ACI/ACC), add it to `CONTRACT_ENTITIES`.
- `docs/reference/entities.md` and `entities.fr.md`: add a row in the right table and keep summaries consistent.

## 4. Test

- Add or extend tests under `tests/` (`tests/conftest.py` provides `config_entry` and `mock_fetch`).
- For API fields, extend `sample_api_response` in `conftest.py` when a new field is needed.
- Run `uv run pytest tests/ -q`.

## 5. Finish

- `CHANGELOG.md` and `CHANGELOG.fr.md` → new bullet under `[Unreleased]` / `[Non publié]`.
- Update `README.md`/`README.fr.md` only if the entity is user-facing enough to appear in the feature list.
- `prek run --all-files` must pass.

## Rules

- Never duplicate an existing helper or description pattern; reuse first (see AGENTS.md).
- No entity may be added without its translations, icon and docs in the same change.
- Diagnostic/informational entities use `EntityCategory.DIAGNOSTIC`; use `entity_registry_visible_default=False` for noisy raw fields.
- When removing an entity instead, delete it together with its translations, icons, tests, docs and changelog entry — no dead code.
