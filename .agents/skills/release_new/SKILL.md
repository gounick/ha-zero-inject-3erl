---
name: release_new
description: Prepare and publish a new release — pick the next SemVer, bump version files, tag and create the GitHub release
---

Create a new release of this repository end to end.

## 1. Determine the next version

- Run `git tag --sort=-v:refname` and read `CHANGELOG.md` to find the latest released version.
- Inspect the `[Unreleased]` section of `CHANGELOG.md`:
  - Breaking changes or removed entities/services → bump **minor** (project is pre-1.0).
  - New features → **minor**.
  - Fixes and docs only → **patch**.
- If the choice is ambiguous, ask the user before proceeding.
- The resulting version must be plain SemVer `X.Y.Z` (no `v` prefix in files; the tag uses `vX.Y.Z`).

## 2. Bump version files

- Run `RELEASE_VERSION=X.Y.Z python3 .github/scripts/bump_version.py` from the repo root — it updates `CHANGELOG.md`, `custom_components/*/manifest.json` and `pyproject.toml`.
- Manually apply the same `## [X.Y.Z] - <today>` header to `CHANGELOG.fr.md` (the script only handles the English file) and translate its section if needed.
- Run `uv lock` to resync `uv.lock` with the new `pyproject.toml` version.
- Verify with `RELEASE_VERSION=X.Y.Z python3 .github/scripts/bump_version.py --check` — it must exit 0.

## 3. Validate

- `uv run --frozen pytest tests/ -q`
- `prek run --all-files`
- `git diff --check`

## 4. Commit, tag, release

- Commit message style: `Prepare X.Y.Z release: <short summary>` (see `git log` for history).
- Commit, push `main`, then create and push tag `vX.Y.Z`.
- Create the GitHub release with `gh release create vX.Y.Z --title "X.Y.Z" --generate-notes` (or curated notes translated from the changelog).
- Confirm the `Release checks` workflow goes green on the tag before reporting success.

## Rules

- Never invent a version already used by a tag or a changelog section.
- Do not push or create the GitHub release if any validation step fails.
- Keep `CHANGELOG.md` and `CHANGELOG.fr.md` synchronized.
