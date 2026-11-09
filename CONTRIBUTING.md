# Contributing

Contributions are welcome — PV systems adapters, 3ERL-related integrations, tests and documentation.

## Before opening a pull request

- Open an issue first to discuss the change, unless it is a trivial fix.
- Keep pull requests focused: one problem per PR.

## Requirements for acceptable contributions

The coding standards, architecture rules, testing requirements and documentation
policy are defined in [AGENTS.md](AGENTS.md). In short:

- English for code, comments and documentation; French only in
  `translations/fr.json` and secondary `*.fr.md` documentation files.
- `uv run pytest tests/ -v` must pass; run `prek run --all-files` before submitting.
- Tests must be added or updated for any change in logic or new feature.
- Update `README.md`, `docs/`, `WORKFLOW.md` and `CHANGELOG.md` for
  user-facing or architectural changes.
- Never log or commit secrets or credentials.

## Reporting issues

Use [GitHub Issues](https://github.com/gounick/ha-zero-inject-3erl/issues) for bug
reports and enhancement requests. For security vulnerabilities, do not open a
public issue — follow the [security policy](SECURITY.md) instead.
