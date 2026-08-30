#!/usr/bin/env python3
"""
Fixture Generation Progress Checker

Checks which reference fixtures have been generated and provides a progress report.

Usage:
    python scripts/check_fixtures.py [--verbose]

License: PolyForm Noncommercial 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_fixtures():
    """Check fixture generation status."""
    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures" / "cross_platform"
    test_cases_file = fixtures_dir / "test_cases.json"

    if not test_cases_file.exists():
        print(f"❌ Test cases file not found: {test_cases_file}")
        return 1

    # Load test cases
    with open(test_cases_file, encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data["test_cases"]
    total = len(test_cases)

    print("=" * 70)
    print("FIXTURE GENERATION PROGRESS")
    print("=" * 70)
    print()

    generated = []
    missing = []

    for test_case in test_cases:
        name = test_case["name"]
        fixture_dir = fixtures_dir / name
        reference_stl = fixture_dir / "reference.stl"
        params_json = fixture_dir / "params.json"

        # Check status
        has_stl = reference_stl.exists()
        has_params = params_json.exists()

        if has_stl:
            generated.append(
                {
                    "name": name,
                    "stl_size": reference_stl.stat().st_size,
                    "has_params": has_params,
                    "priority": test_case.get("priority", "medium"),
                    "description": test_case.get("description", ""),
                }
            )
        else:
            missing.append(
                {
                    "name": name,
                    "priority": test_case.get("priority", "medium"),
                    "description": test_case.get("description", ""),
                    "has_dir": fixture_dir.exists(),
                    "has_params": has_params,
                }
            )

    # Print generated fixtures
    if generated:
        print(f"✅ GENERATED ({len(generated)}/{total}):")
        print()
        for fixture in sorted(
            generated, key=lambda x: (x["priority"] != "high", x["name"])
        ):
            priority_marker = "🔥" if fixture["priority"] == "high" else "  "
            size_mb = fixture["stl_size"] / 1024 / 1024
            print(f"  {priority_marker} {fixture['name']}")
            print(f"     Size: {size_mb:.2f} MB")
            print(f"     {fixture['description']}")
            if not fixture["has_params"]:
                print("     ⚠️  Warning: params.json missing")
            print()

    # Print missing fixtures
    if missing:
        print(f"❌ MISSING ({len(missing)}/{total}):")
        print()
        for fixture in sorted(
            missing, key=lambda x: (x["priority"] != "high", x["name"])
        ):
            priority_marker = "🔥" if fixture["priority"] == "high" else "  "
            print(f"  {priority_marker} {fixture['name']}")
            print(f"     {fixture['description']}")
            if not fixture["has_dir"]:
                print("     ⚠️  Directory not created yet")
            if fixture["has_params"]:
                print("     ✓ params.json exists (copy parameters from this file)")
            print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    percent = (len(generated) / total * 100) if total > 0 else 0
    print(f"Progress: {len(generated)}/{total} ({percent:.0f}%)")
    print()

    if len(generated) == 0:
        print("⚠️  No fixtures generated yet")
        print()
        print("Next steps:")
        print("  Run: python scripts/regenerate_fixtures.py --openscad-mode")
        print("  See: tests/README.md for details")
        print()
    elif len(missing) > 0:
        high_priority_missing = [f for f in missing if f["priority"] == "high"]
        if high_priority_missing:
            print("⚠️  High priority fixtures still missing:")
            for fixture in high_priority_missing:
                print(f"     - {fixture['name']}")
            print()

        print("Next steps:")
        print(f"  Generate remaining {len(missing)} fixture(s)")
        print("  Run: python scripts/regenerate_fixtures.py --openscad-mode")
        print()
    else:
        print("✅ All fixtures generated!")
        print()
        print("Next steps:")
        print("  1. Verify: python scripts/validate_setup.py")
        print("  2. Run tests: pytest tests/cross_platform_validation.py -v")
        print()

    print("=" * 70)

    return 0 if len(missing) == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check fixture generation progress")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        return check_fixtures()
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
