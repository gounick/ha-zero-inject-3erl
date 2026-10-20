"""Prepare CHANGELOG.md and manifest.json for a release.

The version is read from the RELEASE_VERSION environment variable, never
interpolated into code, and must be a plain PEP 440 release such as 1.2.3 or
1.2.3rc1 (a leading "v" is accepted). The normalized version is written to
GITHUB_OUTPUT as ``version``.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?")
UNRELEASED_HEADER = "## [Unreleased]"


def update_changelog(path: Path, version: str) -> None:
    """Insert a release header under the Unreleased section once.

    :param path: Path of CHANGELOG.md.
    :type path: Path
    :param version: Validated release version.
    :type version: str
    """
    text = path.read_text(encoding="utf-8")
    if f"## [{version}]" in text:
        return
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    release_header = f"{UNRELEASED_HEADER}\n\n## [{version}] - {today}"
    path.write_text(text.replace(UNRELEASED_HEADER, release_header, 1), encoding="utf-8")


def update_manifests(root: Path, version: str) -> None:
    """Set the version of every integration manifest.

    :param root: Directory containing the integrations.
    :type root: Path
    :param version: Validated release version.
    :type version: str
    """
    for manifest in root.glob("*/manifest.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["version"] = version
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    """Validate the version and update the release files.

    :return: Process exit code.
    :rtype: int
    """
    version = os.environ.get("RELEASE_VERSION", "").strip().removeprefix("v")
    if not VERSION_PATTERN.fullmatch(version):
        print(f"Invalid release version: {version!r}", file=sys.stderr)
        return 1

    update_changelog(Path("CHANGELOG.md"), version)
    update_manifests(Path("custom_components"), version)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"version={version}\n")
    print(f"Prepared release {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
