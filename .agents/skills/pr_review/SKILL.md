---
name: pr_review
description: Review a branch or pull request against this repository's house rules — AGENTS.md principles, bilingual docs, translations, tests and changelog — before merge
---

Review the current branch (or a PR given by number) as a maintainer of this repository would. Report findings ordered by severity; do not approve silently.

## 1. Gather the diff

- `git fetch origin && git diff origin/main...HEAD` (or `gh pr diff <n>`).
- `git log origin/main..HEAD` for the commit list and message style.
- Check for unrelated or bundled changes: one problem per PR.

## 2. House-rules checklist

- **English everywhere** in code, comments, docstrings and docs; only `*.fr.md` files and `translations/fr.json` hold French.
- **Bilingual docs**: every changed `*.md` has its `.fr.md` twin updated; `translations/en.json` and `fr.json` keep identical key trees (`tests/test_i18n.py` enforces it — still review wording quality).
- **DRY**: no duplicated logic; reuse `helpers.py` (curtailment decision, mode resolution, `entry_settings`, `build_device_info`).
- **KISS**: simplest readable solution; no premature abstraction.
- **No dead code**: no unused functions/constants, no commented-out blocks, no "just in case" fallback paths. `vulture` runs in prek but only scans `custom_components`.
- Docstrings in Sphinx format on new public functions.
- No secrets or credentials logged.
- `sensor.py`/`binary_sensor.py` read `coordinator.data`, never the API.
- `CHANGELOG.md` and `CHANGELOG.fr.md` both have an `[Unreleased]`/`[Non publié]` entry for user-facing changes.
- `services.yaml`, `icons.json`, translations and `docs/reference/*.md` updated together with any entity or service change.
- Brand images only under `custom_components/zero_inject_3erl/brand/` — never PRs to `home-assistant/brands`.

## 3. Verify

- `uv run pytest tests/ -q` — all tests pass; new logic has new tests.
- `prek run --all-files` — clean.
- `git diff --check` — no whitespace errors.
- `uv run python3 -m py_compile` on changed Python files if anything looks odd.

## 4. Report

For each finding: file:line, severity (blocker / should-fix / nit), and the concrete fix. Finish with a verdict: approve, request changes, or needs discussion.

## Rules

- Review the diff, not the intent: claims in the PR body must match the code.
- A green CI does not waive the bilingual-docs and changelog checks.
- If the change breaks users, require a `CHANGELOG.md` "Changed"/"Removed" note — breaking changes are acceptable only when announced.
