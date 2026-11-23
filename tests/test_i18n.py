"""Repository hygiene checks for the bilingual documentation rules."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "custom_components" / "zero_inject_3erl" / "translations"

# Agent tooling stays English-only; the AGENTS.md bilingual rule covers
# user-facing documentation, not skill files.
EXCLUDED_PREFIXES = (".agents/",)


def _key_paths(tree: Any, prefix: str = "") -> set[str]:
    """Return the set of dotted key paths of a nested mapping."""
    if not isinstance(tree, dict):
        return {prefix}
    paths: set[str] = set()
    for key, value in tree.items():
        paths |= _key_paths(value, f"{prefix}.{key}" if prefix else key)
    return paths


def test_translation_key_parity() -> None:
    """Test that en.json and fr.json expose the same key tree."""
    en = json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8"))
    fr = json.loads((TRANSLATIONS / "fr.json").read_text(encoding="utf-8"))
    assert _key_paths(en) == _key_paths(fr)


def test_every_markdown_doc_has_a_french_twin() -> None:
    """Test that every tracked Markdown file has a sibling *.fr.md version."""
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    missing = [
        path
        for path in result.stdout.splitlines()
        if not path.endswith(".fr.md")
        and not path.startswith(EXCLUDED_PREFIXES)
        and not (ROOT / path).with_suffix(".fr.md").exists()
    ]
    assert missing == []
