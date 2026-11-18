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

## 4. Commit, open a release PR, tag, release

`main` is protected: never push the release commit directly. Route it through a pull request.

- Commit message style: `Prepare X.Y.Z release: <short summary>` (see `git log` for history).
- Create a release branch `release/vX.Y.Z`, commit there and push it.
- Open the PR: `gh pr create --base main --title "Prepare X.Y.Z release: <short summary>" --body <changelog section>` and wait for the required checks to go green (`gh pr checks --watch`). Do not merge while checks are pending or failing.
- Merge the PR (`gh pr merge --merge`), then `git checkout main && git pull` so the tag points at the merged commit.
- Create and push tag `vX.Y.Z` on the merged `main` commit.
- Create the GitHub release with `gh release create vX.Y.Z --title "X.Y.Z" --generate-notes` (or curated notes translated from the changelog).
- Confirm the `Release checks` workflow goes green on the tag before reporting success.
- Delete the release branch after the merge (`gh pr merge --delete-branch` or `git push origin --delete release/vX.Y.Z`).

## Rules

- Never invent a version already used by a tag or a changelog section.
- Do not push to `main` directly — branch protection requires a PR; only the tag is pushed.
- Do not merge the release PR or create the GitHub release if any validation step or PR check fails.
- Keep `CHANGELOG.md` and `CHANGELOG.fr.md` synchronized.
