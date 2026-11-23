---
name: release_verify
description: Post-release verification — confirm the tag, GitHub release, workflows and HACS package content are consistent after /release_new
---

Run after a release was published (typically after `/release_new`). Verify the release is consistent and complete; report each check as OK or FAIL.

## 1. Tag and version consistency

- `git fetch --tags origin` then `git tag --sort=-v:refname | head -1` — the latest tag is `vX.Y.Z` matching the release being verified.
- `custom_components/zero_inject_3erl/manifest.json` `"version"` equals `X.Y.Z` (no `v`).
- `pyproject.toml` `version` equals `X.Y.Z`.
- `CHANGELOG.md` and `CHANGELOG.fr.md` both contain a `## [X.Y.Z] - <date>` section with matching content.

## 2. GitHub release

- `gh release view vX.Y.Z` — release exists, is not a draft, has notes.
- `gh release view vX.Y.Z --json assets` — the expected assets/archives are present.

## 3. Workflows

- `gh run list --limit 10` — the `Release checks` workflow (and `hassfest`/`hacs` validation if triggered by the tag) is green on the tagged commit.
- `gh run view <run-id>` for any failed run: report the failing step.

## 4. Package content

- The release archive (or the tagged tree) contains `custom_components/zero_inject_3erl/` complete with `manifest.json`, `translations/`, `services.yaml`, `icons.json` and `brand/`.
- `hacs.json` is valid and points at the right repository.

## 5. Report

Emit a table: check → OK/FAIL → evidence (command output or URL). On any FAIL, open a GitHub issue describing the gap instead of fixing it silently.

## Rules

- Never create, retag or delete a release from this skill — verification only.
- If versions disagree, stop and report; do not bump files here.
