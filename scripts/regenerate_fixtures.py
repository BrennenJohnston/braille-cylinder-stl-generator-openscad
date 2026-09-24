"""
Regenerate Reference Fixtures for STL Validation

This script generates reference STL files to serve as golden fixtures
for regression testing and validation.

Supports two modes:
1. OpenSCAD Mode (default): Uses OpenSCAD to generate reference STLs
   - Self-test mode for internal consistency validation
   - No external dependencies

2. Web API Mode (deprecated): Uses web generator API
   - Requires running web server (deprecated as of 2026-01-05)

Usage:
    # OpenSCAD mode (recommended)
    python scripts/regenerate_fixtures.py --openscad-mode

    # Generate specific fixture
    python scripts/regenerate_fixtures.py --openscad-mode --test-case card_rounded_emboss_basic

    # Web API mode (deprecated, will fail)
    python scripts/regenerate_fixtures.py --web-api-url http://localhost:5000

License: PolyForm Noncommercial 1.0.0
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path BEFORE importing project modules, so E402 is
# expected on the imports below.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import trimesh  # noqa: E402

from tests.openscad_runner import OpenSCADNotFoundError, OpenSCADRunner  # noqa: E402

logger = logging.getLogger(__name__)


class OpenSCADFixtureGenerator:
    """Generate reference fixtures using OpenSCAD CLI."""

    def __init__(self, scad_file: Path, output_dir: Path):
        """
        Initialize OpenSCAD fixture generator.

        Args:
            scad_file: Path to OpenSCAD file
            output_dir: Output directory for fixtures
        """
        self.scad_file = scad_file
        self.output_dir = output_dir
        self.runner = OpenSCADRunner()

        logger.info(f"OpenSCAD version: {self.runner.get_version()}")

    def generate_fixture(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate reference fixture for a test case.

        Args:
            test_case: Test case definition

        Returns:
            Fixture metadata
        """
        test_name = test_case["name"]
        parameters = test_case["parameters"]

        logger.info(f"Generating fixture: {test_name}")

        # Create fixture directory
        fixture_dir = self.output_dir / test_name
        fixture_dir.mkdir(parents=True, exist_ok=True)

        # Generate STL using OpenSCAD
        stl_path = fixture_dir / "reference.stl"

        result = self.runner.generate_stl(
            scad_file=self.scad_file,
            output_stl=stl_path,
            parameters=parameters,
            timeout_seconds=300,
        )

        if not result.success:
            raise RuntimeError(
                f"OpenSCAD failed for {test_name}:\n"
                f"  Command: {result.command}\n"
                f"  Return code: {result.returncode}\n"
                f"  Stderr: {result.stderr}"
            )

        logger.info(f"  Generated in {result.duration_seconds:.1f}s")

        # Read STL content for checksum
        stl_content = stl_path.read_bytes()
        checksum = hashlib.sha256(stl_content).hexdigest()

        # Extract mesh properties using trimesh
        mesh = trimesh.load(stl_path, force="mesh")
        mesh_properties = {
            "volume_mm3": float(mesh.volume),
            "surface_area_mm2": float(mesh.area),
            "bounding_box_mm": mesh.bounds.tolist(),
            "face_count": len(mesh.faces),
            "vertex_count": len(mesh.vertices),
            "is_watertight": mesh.is_watertight,
            "centroid_mm": mesh.centroid.tolist(),
        }

        logger.info(f"  Volume: {mesh_properties['volume_mm3']:.2f} mm³")
        logger.info(f"  Faces: {mesh_properties['face_count']}")
        logger.info(f"  Watertight: {mesh_properties['is_watertight']}")

        # Save parameters
        params_path = fixture_dir / "params.json"
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_case": test_name,
                    "parameters": parameters,
                    "generated_with": "openscad",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Create metadata
        metadata = {
            "test_name": test_name,
            "description": test_case.get("description", ""),
            "tags": test_case.get("tags", []),
            "priority": test_case.get("priority", "medium"),
            "reference_stl": f"cross_platform/{test_name}/reference.stl",
            "stl_size_bytes": len(stl_content),
            "stl_sha256": checksum,
            "mesh_properties": mesh_properties,
            "generation": {
                "method": "openscad",
                "openscad_version": self.runner.get_version(),
                "scad_file": str(self.scad_file.name),
                "duration_seconds": result.duration_seconds,
            },
            "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }

        # Save metadata
        metadata_path = fixture_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def generate_all_fixtures(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate all reference fixtures.

        Args:
            test_cases: List of test case definitions

        Returns:
            Summary metadata for all fixtures
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        fixtures_metadata = []
        failed_cases = []

        for test_case in test_cases:
            test_name = test_case["name"]
            try:
                metadata = self.generate_fixture(test_case)
                fixtures_metadata.append(metadata)
                logger.info(f"  ✓ {test_name}")
            except Exception as e:
                logger.error(f"  ✗ {test_name}: {e}")
                failed_cases.append({"name": test_name, "error": str(e)})

        # Create version file
        version_info = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "generation_method": "openscad",
            "openscad_version": self.runner.get_version(),
            "scad_file": str(self.scad_file.name),
            "total_fixtures": len(fixtures_metadata),
            "failed_fixtures": len(failed_cases),
            "fixtures": fixtures_metadata,
        }

        if failed_cases:
            version_info["failures"] = failed_cases

        # Save version files
        version_txt_path = self.output_dir / "FIXTURES_VERSION.txt"
        with open(version_txt_path, "w") as f:
            f.write("# Reference Fixture Version Information\n")
            f.write(f"# Generated: {version_info['generated_at']}\n")
            f.write("# Method: OpenSCAD self-test mode\n")
            f.write(f"# OpenSCAD: {version_info['openscad_version']}\n")
            f.write(f"# Total fixtures: {version_info['total_fixtures']}\n")
            f.write(f"# Failed: {version_info['failed_fixtures']}\n")
            f.write("\n")
            f.write("# See FIXTURES_VERSION.json for full metadata\n")

        version_json_path = self.output_dir / "FIXTURES_VERSION.json"
        with open(version_json_path, "w") as f:
            json.dump(version_info, f, indent=2)

        return version_info


class WebAPIFixtureGenerator:
    """Generate reference fixtures from web generator API (DEPRECATED)."""

    def __init__(self, web_api_url: str):
        """
        Initialize web API fixture generator.

        Args:
            web_api_url: Base URL of web generator API
        """
        import requests

        self.web_api_url = web_api_url.rstrip("/")
        self.session = requests.Session()

    def check_api_health(self) -> bool:
        """Check if web API is accessible."""
        import requests

        try:
            response = self.session.get(f"{self.web_api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ Web API is accessible: {self.web_api_url}")
                return True
            elif response.status_code == 410:
                logger.error(
                    "Web API has been deprecated (410 Gone).\n"
                    "The server-side STL generation was removed on 2026-01-05.\n"
                    "Use --openscad-mode instead for self-test fixture generation."
                )
                return False
            else:
                logger.error(f"Web API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot reach web API: {e}")
            return False

    def generate_stl(self, parameters: Dict[str, Any]) -> bytes:
        """Generate STL from web API (deprecated)."""
        import requests

        try:
            response = self.session.post(
                f"{self.web_api_url}/generate_braille_stl",
                json=parameters,
                timeout=60,
            )

            if response.status_code == 410:
                raise RuntimeError(
                    "Web API deprecated (410 Gone). "
                    "Use --openscad-mode for fixture generation."
                )
            elif response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    error_data = response.json()
                    raise RuntimeError(f"API returned error: {error_data}")
                return response.content
            else:
                raise RuntimeError(
                    f"API request failed with status {response.status_code}: "
                    f"{response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate reference fixtures for STL validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate all fixtures using OpenSCAD (recommended)
    python scripts/regenerate_fixtures.py --openscad-mode
    
    # Generate specific fixture
    python scripts/regenerate_fixtures.py --openscad-mode --test-case card_rounded_emboss_basic
    
    # List available test cases
    python scripts/regenerate_fixtures.py --list-cases
        """,
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--openscad-mode",
        action="store_true",
        default=True,
        help="Use OpenSCAD to generate fixtures (default, recommended)",
    )
    mode_group.add_argument(
        "--web-api-url",
        help="Web generator API URL (deprecated - will likely fail)",
    )

    # Options
    parser.add_argument(
        "--test-case",
        help="Generate only a specific test case (by name)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "tests" / "fixtures" / "cross_platform",
        help="Output directory for fixtures",
    )
    parser.add_argument(
        "--test-cases-file",
        type=Path,
        default=PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "cross_platform"
        / "test_cases.json",
        help="Test cases definition file",
    )
    parser.add_argument(
        "--scad-file",
        type=Path,
        default=PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad",
        help="OpenSCAD file to use (for --openscad-mode)",
    )
    parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List available test cases and exit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if tools are available",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        # Load test cases
        with open(args.test_cases_file, encoding="utf-8") as f:
            test_cases_data = json.load(f)
        test_cases = test_cases_data["test_cases"]

        # List cases if requested
        if args.list_cases:
            print("\nAvailable test cases:")
            print("-" * 60)
            for tc in test_cases:
                print(f"  {tc['name']}")
                print(f"    Description: {tc['description']}")
                print(f"    Priority: {tc['priority']}")
                print(f"    Tags: {', '.join(tc['tags'])}")
                print()
            return 0

        # Filter to specific test case if requested
        if args.test_case:
            test_cases = [tc for tc in test_cases if tc["name"] == args.test_case]
            if not test_cases:
                logger.error(f"Test case not found: {args.test_case}")
                logger.info("Use --list-cases to see available test cases")
                return 1

        # Choose generation mode
        if args.web_api_url:
            # Web API mode (deprecated)
            logger.warning("=" * 70)
            logger.warning("WARNING: Web API mode is DEPRECATED")
            logger.warning("The web generator API was removed on 2026-01-05")
            logger.warning("Use --openscad-mode instead (recommended)")
            logger.warning("=" * 70)

            generator = WebAPIFixtureGenerator(args.web_api_url)
            if not generator.check_api_health():
                logger.error("Web API is not accessible.")
                logger.info("Use --openscad-mode for local fixture generation.")
                return 1

            if args.check_only:
                logger.info("✓ Web API check complete (but deprecated)")
                return 0

            logger.error("Web API fixture generation not supported (deprecated)")
            return 1

        else:
            # OpenSCAD mode (default, recommended)
            logger.info("=" * 70)
            logger.info("OpenSCAD Self-Test Fixture Generation")
            logger.info("=" * 70)

            if not args.scad_file.exists():
                logger.error(f"OpenSCAD file not found: {args.scad_file}")
                return 1

            try:
                generator = OpenSCADFixtureGenerator(
                    scad_file=args.scad_file,
                    output_dir=args.output_dir,
                )
            except OpenSCADNotFoundError as e:
                logger.error(f"OpenSCAD not found: {e}")
                logger.info(
                    "Please install OpenSCAD: https://openscad.org/downloads.html"
                )
                return 1

            if args.check_only:
                logger.info("✓ OpenSCAD check complete")
                return 0

            # Generate fixtures
            logger.info(f"Generating {len(test_cases)} fixture(s)...")
            logger.info(f"Output directory: {args.output_dir}")
            logger.info("")

            version_info = generator.generate_all_fixtures(test_cases)

            # Print summary
            print("\n" + "=" * 70)
            print("FIXTURE GENERATION COMPLETE")
            print("=" * 70)
            print(f"  Generated: {version_info['total_fixtures']}")
            print(f"  Failed: {version_info['failed_fixtures']}")
            print("  Method: OpenSCAD self-test")
            print(f"  OpenSCAD: {version_info['openscad_version']}")
            print(f"  Output: {args.output_dir}")
            print("=" * 70)

            if version_info["failed_fixtures"] > 0:
                logger.warning("Some fixtures failed to generate")
                return 1

            logger.info("✓ All fixtures generated successfully")
            return 0

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
