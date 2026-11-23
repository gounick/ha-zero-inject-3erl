---
name: bugfix
description: Fix a bug the house way — reproduce with a failing test first, fix minimally, run the suite, update the changelog in both languages
---

Fix a reported bug in this repository following the project's test-first discipline.

## 1. Reproduce

- Restate the bug in one sentence: input/context → expected → actual.
- Write a failing test under `tests/` proving it. Reuse `tests/conftest.py` fixtures: `config_entry`, `mock_fetch`, `sample_api_response`, `fresh_heure_update`; `async_mock_service` and `async_fire_time_changed` from `pytest_homeassistant_custom_component.common` for service calls and time.
- Run it: `uv run pytest tests/<file> -q` — it must FAIL for the right reason (the missing/wrong behavior, not a typo).

## 2. Fix

- Implement the minimal fix in `custom_components/zero_inject_3erl/`.
- Reuse existing helpers (`helpers.py`, `entry_settings`, coordinator properties) instead of duplicating logic.
- Re-run the failing test — it must pass.

## 3. Guard the suite

- `uv run pytest tests/ -q` — the whole suite, not just your test.
- `prek run --all-files` — lint, format and vulture clean.

## 4. Document

- `CHANGELOG.md` → bullet under `[Unreleased]` → `### Fixed`.
- `CHANGELOG.fr.md` → matching bullet under `[Non publié]` → `### Corrigé`.
- Update `docs/` EN+FR only when the fix changes documented behavior.

## 5. Commit

- English commit message: `Fix: <what was wrong>` or the repo's existing style.
- Mention the user-visible symptom, not just the code change.

## Rules

- No production change without a failing test first.
- If the bug cannot be reproduced in a test, say so explicitly and ask how to reproduce it on a real instance before editing code.
- Do not leave the old buggy path as a fallback — delete it (no dead code).
