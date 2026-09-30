# AGENTS.md

This file provides guidance to compatible agentic tools when generating or reviewing code in this repository.

**Note:** This file is for AI assistant use only. For human developers, refer to the project's contribution guide.

---

## Important: Always Start Here

1. **Read this file first** — Do not work from memory or assumptions.
2. **Scan the existing codebase** — Identify utilities, helpers and patterns already available.
3. **Follow the principles below** — They are non-negotiable.
4. **Self-check before responding** — Use the checklist at the bottom of this file.

---

## Core Principles

### Use English Everywhere

- Always use English for code, comments, documentation, and user-facing messages.
- No French or other languages, except in the French translation file (`translations/fr.json`).

### DRY — Don't Repeat Yourself

- Never duplicate logic. Reuse or extend existing functions before writing new ones.
- Extract shared logic into helpers when the same pattern appears twice.
- Examples of shared concepts:
  - Curtailment decision (`is_curtailment_active`) lives in the coordinator.
  - Mode resolution uses the select entity state; prefer reading it once and propagating the result.

### KISS — Keep It Simple, Stupid

- Prefer the simplest readable solution.
- Avoid premature abstraction.

### Documentation & Changelog

- Update `README.md` when adding or changing features visible to users.
- Update `docs/*.md` and `WORKFLOW.md` when changing wiring, Envoy setup, dashboard examples or architecture.
- Add an entry to `CHANGELOG.md` at the repository root for every user-facing or architectural change.

---

## Before Writing Any Code

1. Scan existing utilities under `custom_components/zero_inject_3erl/`.
2. Check for similar patterns in other Home Assistant integrations in this repo.
3. Reuse before creating.
4. If you need to add a new PV system adapter, read the extensibility notes below first.

---

## Code Style

- Keep functions short and focused (ideally under 20–30 lines).
- Use explicit, descriptive names.
- No dead code, no commented-out blocks, no trailing whitespace.
- Write Sphinx-format docstrings (`:param name:`, `:type name:`, `:return:`, `:rtype:`).
- Never log secrets or credentials.
- Always use Python 3 exception syntax.

---

## Project Architecture

```
custom_components/zero_inject_3erl/
├── __init__.py       # HA lifecycle, service registration
├── manifest.json     # Integration metadata
├── const.py          # Domain constants, config keys, defaults
├── config_flow.py    # UI configuration flow + options flow
├── api.py            # 3ERL REST API client
├── coordinator.py    # DataUpdateCoordinator, energy/gain accumulation
├── controller.py     # Relay control logic (Auto / On / Off)
├── sensor.py         # API + computed sensors
├── binary_sensor.py  # Bridage demandé, Bridage CDC, Zero-Inject actif
├── select.py         # Mode selector
├── services.yaml     # Service definitions
└── translations/     # UI translations
```

- `ThreeERLApiClient` owns all HTTP calls to `https://3erl.fr/api.json`.
- `ThreeERLUpdateCoordinator` polls the API and accumulates curtailed energy/gain from the configured PV power sensor.
- `ZeroInjectController` listens to coordinator updates and mode changes, then turns the relay on or off.
- `sensor.py` and `binary_sensor.py` must not call the API directly; they read `coordinator.data`.

### Extensibility for other PV systems

Currently the integration supports a generic PV power sensor. Future providers (Enphase auto-detection, SMA, Fronius, etc.) should be added as adapter modules under `custom_components/zero_inject_3erl/providers/`, each exposing:

- `is_supported(hass, entry)` — detect whether this provider applies.
- `async_get_power_entity(hass, entry)` — return the power sensor entity ID to monitor.

The coordinator and controller should remain provider-agnostic.

---

## Testing & Quality

- Run `python3 -m py_compile <file>` for every changed Python file.
- If `prek` or `pre-commit` is configured, run the full check suite (`prek run --all-files`).
- Add or update tests when modifying logic or adding features.

### Development environment with uv

This project uses `uv` to manage the Python environment and dependencies.

```bash
# Sync dev dependencies (lint/test tools).
uv sync --extra test

# Run tests.
uv run pytest tests/ -v

# Run hooks.
prek run --all-files

# Compile changed Python files for syntax checks.
uv run python3 -m py_compile <modified_files>
```

---

## Self-Check Before Submitting

```
□ Is there an existing function that already handles this logic?
□ Am I duplicating code that exists elsewhere in the project?
□ Is this the simplest solution that works?
□ Did I remove all unused code and trailing whitespace?
□ Are credentials or secrets never logged or hard-coded?
□ Have I updated README.md, docs/*.md, WORKFLOW.md and CHANGELOG.md?
□ Did I add or update tests for the changed logic?
```

If the answer to any of these questions is **no**, revise before submitting.
