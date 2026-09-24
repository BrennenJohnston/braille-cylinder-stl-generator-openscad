#!/usr/bin/env python3
"""
Fixture Integrity Verifier

Validates that reference fixture STL files match the recorded size and SHA256
checksums in:
- tests/fixtures/cross_platform/FIXTURES_VERSION.json
- tests/fixtures/cross_platform/<case>/metadata.json

This is a lightweight sanity check to confirm checked-in fixtures and their
metadata are coherent (useful for CI/debugging).

Exit codes:
- 0: all checks passed
- 1: one or more integrity issues found
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(fixtures_root: Path) -> List[str]:
    issues: List[str] = []

    version_path = fixtures_root / "FIXTURES_VERSION.json"
    if not version_path.exists():
        return [f"Missing {version_path}"]

    version = _load_json(version_path)
    fixtures = version.get("fixtures", [])

    if not isinstance(fixtures, list) or not fixtures:
        return [f"No fixtures listed in {version_path}"]

    for fx in fixtures:
        name = fx.get("test_name")
        if not name:
            issues.append("Fixture entry missing test_name in FIXTURES_VERSION.json")
            continue

        stl_path = fixtures_root / name / "reference.stl"
        if not stl_path.exists():
            issues.append(f"{name}: missing reference.stl ({stl_path})")
            continue

        stl_bytes = stl_path.read_bytes()
        actual_size = len(stl_bytes)
        actual_sha = _sha256_bytes(stl_bytes)

        exp_size = fx.get("stl_size_bytes")
        exp_sha = fx.get("stl_sha256")

        if exp_size is not None and actual_size != exp_size:
            issues.append(
                f"{name}: size mismatch vs FIXTURES_VERSION.json (expected {exp_size}, got {actual_size})"
            )
        if exp_sha is not None and actual_sha != exp_sha:
            issues.append(
                f"{name}: sha256 mismatch vs FIXTURES_VERSION.json (expected {exp_sha}, got {actual_sha})"
            )

        meta_path = fixtures_root / name / "metadata.json"
        if not meta_path.exists():
            issues.append(f"{name}: missing metadata.json ({meta_path})")
            continue

        meta = _load_json(meta_path)
        meta_size = meta.get("stl_size_bytes")
        meta_sha = meta.get("stl_sha256")

        if meta_size is not None and actual_size != meta_size:
            issues.append(
                f"{name}: size mismatch vs metadata.json (expected {meta_size}, got {actual_size})"
            )
        if meta_sha is not None and actual_sha != meta_sha:
            issues.append(
                f"{name}: sha256 mismatch vs metadata.json (expected {meta_sha}, got {actual_sha})"
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify fixture checksums and sizes")
    parser.add_argument(
        "--fixtures-root",
        type=Path,
        default=Path("tests") / "fixtures" / "cross_platform",
        help="Path to tests/fixtures/cross_platform",
    )
    args = parser.parse_args()

    issues = verify(args.fixtures_root)
    print(f"Fixture integrity: issues={len(issues)}")
    if issues:
        print("---")
        for item in issues:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
