"""
Generate Web Reference Fixtures using Playwright

This script generates reference STL files from the web generator UI
by automating browser interactions to download STLs with specific parameters.

This is the FALLBACK approach since the web API was deprecated (410 Gone as of 2026-01-05).
The PREFERRED approach would be to run the web generator source code headlessly,
but this Playwright automation provides a working alternative.

Usage:
    # Install Playwright browsers first (one-time setup)
    python -m playwright install chromium
    
    # Generate all fixtures from web UI
    python scripts/generate_web_fixtures.py --web-url https://braille-stl-generator.example.com
    
    # Generate specific fixture
    python scripts/generate_web_fixtures.py --web-url https://braille-stl-generator.example.com --test-case cylinder_rounded_emboss_indicators_on
    
    # Dry run (check without downloading)
    python scripts/generate_web_fixtures.py --web-url https://braille-stl-generator.example.com --dry-run

Requirements:
    pip install playwright
    python -m playwright install chromium

License: PolyForm Noncommercial 1.0.0
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


class WebFixtureGenerator:
    """Generate reference fixtures from web UI using Playwright automation."""

    def __init__(self, web_url: str, download_dir: Path, headless: bool = True):
        """
        Initialize web fixture generator.

        Args:
            web_url: Base URL of web generator
            download_dir: Directory for downloaded STL files
            headless: Run browser in headless mode
        """
        # Import purely to probe availability, hence unused (F401).
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError:
            raise ImportError(
                "Playwright is required for web fixture generation.\n"
                "Install with: pip install playwright\n"
                "Then run: python -m playwright install chromium"
            )

        self.web_url = web_url.rstrip("/")
        self.download_dir = download_dir
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        """Context manager entry."""
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # Create context with download path
        self.context = self.browser.new_context(
            accept_downloads=True,
            locale="en-US",
            viewport={"width": 1920, "height": 1080},
        )
        
        self.page = self.context.new_page()
        logger.info(f"Browser initialized (headless={self.headless})")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def navigate_to_generator(self) -> bool:
        """
        Navigate to web generator and verify it's loaded.

        Returns:
            True if successful
        """
        try:
            logger.info(f"Navigating to {self.web_url}")
            self.page.goto(self.web_url, wait_until="networkidle", timeout=30000)
            
            # Wait for a stable, always-visible element.
            # NOTE: Some text inputs (e.g., #auto-text) are hidden by default, so waiting
            # on generic textarea/input selectors can flake.
            self.page.wait_for_selector("#action-btn", timeout=15000)
            logger.info("✓ Web generator loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load web generator: {e}")
            return False

    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Set generator parameters in the web UI.

        Args:
            parameters: Test case parameters

        Returns:
            True if successful
        """
        try:
            # This app (see local source templates/index.html) uses:
            # - manual placement inputs: #line1..#lineN (dynamic)
            # - plate_type radios: input[name="plate_type"][value="positive|negative"]
            # - placement_mode radios: input[name="placement_mode"][value="manual|auto"]
            # - shape_type/combined_shape/indicator_shapes radios (in Expert Mode, may be hidden)
            # - single action button (#action-btn) that toggles Generate STL ↔ Download STL

            # Always use MANUAL placement so #line1..#line4 exist
            try:
                self.page.check("input[name='placement_mode'][value='manual']", timeout=3000)
            except Exception:
                pass

            # Plate type
            plate_type = parameters.get("plate_type", "positive")
            try:
                self.page.check(f"input[name='plate_type'][value='{plate_type}']", timeout=3000)
            except Exception as e:
                logger.warning(f"Could not set plate_type '{plate_type}': {e}")

            # Choose contracted UEB table to better match existing braille fixtures
            try:
                self.page.select_option("#language-table", value="en-ueb-g2.ctb", timeout=3000)
            except Exception:
                pass

            # Minimal mapping: braille samples in our OpenSCAD fixtures → English words for web UI
            braille_to_english = {
                "⠞⠑⠌": "test",
                "⠞⠑⠌⠞": "test",
                "⠺⠕⠗": "word",
                "⠺⠕⠗⠙": "word",
                "⠓⠑⠭": "hex",
            }

            # Set Expert-mode radios + numeric fields via JS so hidden inputs still work,
            # and so changing grid_rows happens BEFORE we fill #line1..#line4 (otherwise
            # the app will recreate inputs and wipe our values).
            shape_type = parameters.get("shape_type", "cylinder")
            combined_shape = parameters.get("combined_shape", "rounded")
            indicator_shapes = parameters.get("indicator_shapes", "on")
            indicator_value = "1" if indicator_shapes == "on" else "0"

            self.page.evaluate(
                """
                ({ shapeType, combinedShape, indicatorValue, numeric }) => {
                  const setRadio = (name, value) => {
                    const el = document.querySelector(`input[name="${name}"][value="${value}"]`);
                    if (!el) return false;
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                  };
                  const setInputValue = (id, value) => {
                    if (value === undefined || value === null) return false;
                    const el = document.getElementById(id);
                    if (!el) return false;
                    el.value = String(value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                  };
                  setRadio('shape_type', shapeType);
                  setRadio('combined_shape', combinedShape);
                  setRadio('indicator_shapes', indicatorValue);

                  // Numeric fields: align web generator settings with our test_cases.json
                  // IDs are taken from the local web app template (templates/index.html).
                  Object.entries(numeric || {}).forEach(([id, value]) => setInputValue(id, value));
                }
                """,
                {
                    "shapeType": shape_type,
                    "combinedShape": combined_shape,
                    "indicatorValue": indicator_value,
                    "numeric": {
                        # Braille layout
                        "grid_columns": parameters.get("grid_columns"),
                        "grid_rows": parameters.get("grid_rows"),
                        "cell_spacing": parameters.get("cell_spacing"),
                        "line_spacing": parameters.get("line_spacing"),
                        "dot_spacing": parameters.get("dot_spacing"),
                        "braille_y_adjust": parameters.get("braille_y_adjust"),
                        # Cylinder geometry
                        "cylinder_diameter_mm": parameters.get("cylinder_diameter_mm"),
                        "cylinder_height_mm": parameters.get("cylinder_height_mm"),
                        "cylinder_polygonal_cutout_radius_mm": parameters.get("polygon_cutout_radius_mm"),
                        "cylinder_polygonal_cutout_sides": parameters.get("polygon_cutout_points"),
                        "seam_offset_deg": parameters.get("seam_offset_degrees"),
                        # Rounded dot params
                        "rounded_dot_base_diameter": parameters.get("rounded_dot_base_diameter"),
                        "rounded_dot_base_height": parameters.get("rounded_dot_base_height"),
                        "rounded_dot_dome_height": parameters.get("rounded_dot_dome_height"),
                        "bowl_counter_dot_base_diameter": parameters.get("bowl_counter_dot_base_diameter"),
                        "counter_dot_depth": parameters.get("counter_dot_depth"),
                        # Cone dot params
                        "emboss_dot_base_diameter": parameters.get("emboss_dot_base_diameter"),
                        "emboss_dot_height": parameters.get("emboss_dot_height"),
                        "emboss_dot_flat_hat": parameters.get("emboss_dot_flat_hat"),
                        "cone_counter_dot_base_diameter": parameters.get("cone_counter_dot_base_diameter"),
                        "cone_counter_dot_height": parameters.get("cone_counter_dot_height"),
                        "cone_counter_dot_flat_hat": parameters.get("cone_counter_dot_flat_hat"),
                    },
                },
            )

            # Only positive plates require text input; negative plates are universal in the web app.
            if plate_type == "positive":
                # Ensure dynamic line inputs exist after grid_rows updates
                try:
                    self.page.wait_for_selector("#line1", timeout=15000)
                except Exception:
                    logger.warning("Timed out waiting for #line1 to appear (dynamic inputs)")

                for i in range(1, 5):
                    line_key = f"Line_{i}"
                    raw = parameters.get(line_key, "")
                    value = braille_to_english.get(raw, raw)
                    try:
                        self.page.fill(f"#line{i}", value, timeout=5000)
                    except Exception as e:
                        logger.warning(f"Could not set {line_key} via #line{i}: {e}")

            logger.info("✓ Parameters set")
            return True

        except Exception as e:
            logger.error(f"Failed to set parameters: {e}")
            return False

    def download_stl(self, output_path: Path) -> bool:
        """
        Trigger STL download and save to output path.

        Args:
            output_path: Where to save the downloaded STL

        Returns:
            True if successful
        """
        try:
            # The app uses a single button (#action-btn) which toggles state:
            # - data-state="generate" (Generate STL)
            # - data-state="download" (Download STL)
            action_btn = self.page.wait_for_selector("#action-btn", timeout=15000)
            if not action_btn:
                logger.error("Could not find #action-btn")
                return False

            # Generate
            self.page.click("#action-btn")
            logger.info("Clicked #action-btn to Generate")

            # Wait until it becomes Download state OR a NON-INFO error is displayed.
            # NOTE: During normal generation the app uses #error-message with class "error-message info"
            # as a progress UI. We must not treat that as failure.
            self.page.wait_for_function(
                """() => {
                    const b = document.querySelector('#action-btn');
                    const err = document.getElementById('error-message');
                    const errVisible = err && (getComputedStyle(err).display !== 'none') && (err.textContent || '').trim().length > 0;
                    const errClass = err ? (err.className || '') : '';
                    const isNonInfoError = errVisible && errClass.includes('error-message') && !errClass.includes('info') && !errClass.includes('grade-note');
                    if (!b) return errVisible;
                    const state = b.getAttribute('data-state') || b.dataset.state || '';
                    const txt = (b.textContent || '').toLowerCase();
                    const isDownload = state === 'download' || txt.includes('download stl');
                    return isDownload || isNonInfoError;
                }""",
                timeout=600000,  # allow long client-side CSG (especially counter+cone)
            )

            # If non-info error message is visible, capture it and fail
            try:
                err_text = self.page.evaluate(
                    """() => {
                        const err = document.getElementById('error-message');
                        if (!err) return '';
                        const disp = getComputedStyle(err).display;
                        if (disp === 'none') return '';
                        const cls = err.className || '';
                        if (cls.includes('info') || cls.includes('grade-note')) return '';
                        const t = (document.getElementById('error-text')?.textContent || '').trim();
                        const st = (document.getElementById('error-subtext')?.textContent || '').trim();
                        return [t, st].filter(Boolean).join(' ');
                    }"""
                )
                if err_text:
                    logger.error(f"Web generator error: {err_text}")
                    return False
            except Exception:
                pass

            # Download
            with self.page.expect_download(timeout=180000) as download_info:
                self.page.click("#action-btn")
            download = download_info.value

            output_path.parent.mkdir(parents=True, exist_ok=True)
            download.save_as(output_path)

            logger.info(f"✓ Downloaded STL: {output_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to download STL: {e}")
            return False

    def generate_fixture(
        self, test_case: Dict[str, Any], output_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Generate reference fixture for a test case.

        Args:
            test_case: Test case definition
            output_dir: Output directory for fixtures

        Returns:
            Fixture metadata or None if failed
        """
        test_name = test_case["name"]
        parameters = test_case["parameters"]

        logger.info(f"Generating web fixture: {test_name}")

        # Create fixture directory
        fixture_dir = output_dir / test_name
        fixture_dir.mkdir(parents=True, exist_ok=True)

        # Navigate to generator
        if not self.navigate_to_generator():
            return None

        # Set parameters
        if not self.set_parameters(parameters):
            return None

        # Download STL
        stl_path = fixture_dir / "reference.stl"
        if not self.download_stl(stl_path):
            return None

        # Verify STL file
        if not stl_path.exists() or stl_path.stat().st_size == 0:
            logger.error(f"Downloaded STL is missing or empty: {stl_path}")
            return None

        # Read STL content for checksum
        stl_content = stl_path.read_bytes()
        checksum = hashlib.sha256(stl_content).hexdigest()

        # Extract mesh properties using trimesh
        try:
            import trimesh

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
        except Exception as e:
            logger.warning(f"Could not extract mesh properties: {e}")
            mesh_properties = {}

        # Save parameters
        params_path = fixture_dir / "params.json"
        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_case": test_name,
                    "parameters": parameters,
                    "generated_with": "web_ui",
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
                "method": "web_ui_playwright",
                "web_url": self.web_url,
                "browser": "chromium",
                "headless": self.headless,
            },
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        # Save metadata
        metadata_path = fixture_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate reference fixtures from web UI using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate all fixtures from web UI
    python scripts/generate_web_fixtures.py --web-url https://braille-generator.example.com
    
    # Generate specific fixture
    python scripts/generate_web_fixtures.py --web-url https://example.com --test-case cylinder_rounded_emboss_indicators_on
    
    # Dry run (check without downloading)
    python scripts/generate_web_fixtures.py --web-url https://example.com --dry-run
    
    # Run with visible browser (for debugging)
    python scripts/generate_web_fixtures.py --web-url https://example.com --no-headless

Setup:
    pip install playwright
    python -m playwright install chromium
        """,
    )

    parser.add_argument(
        "--web-url",
        required=True,
        help="Base URL of web generator (e.g., https://braille-generator.example.com)",
    )
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
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (for debugging)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check setup without generating fixtures",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        # Check Playwright installation. Imported only to probe availability.
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError:
            logger.error("Playwright is not installed.")
            logger.info("Install with: pip install playwright")
            logger.info("Then run: python -m playwright install chromium")
            return 1

        # Load test cases
        with open(args.test_cases_file, encoding="utf-8") as f:
            test_cases_data = json.load(f)
        test_cases = test_cases_data["test_cases"]

        # Filter to specific test case if requested
        if args.test_case:
            test_cases = [tc for tc in test_cases if tc["name"] == args.test_case]
            if not test_cases:
                logger.error(f"Test case not found: {args.test_case}")
                return 1

        if args.dry_run:
            logger.info("=" * 70)
            logger.info("DRY RUN - Setup Check")
            logger.info("=" * 70)
            logger.info(f"Web URL: {args.web_url}")
            logger.info(f"Test cases: {len(test_cases)}")
            logger.info(f"Output dir: {args.output_dir}")
            logger.info("✓ Playwright installed")
            logger.info("=" * 70)
            logger.info("Run without --dry-run to generate fixtures")
            return 0

        # Generate fixtures
        logger.info("=" * 70)
        logger.info("Web UI Fixture Generation (Playwright)")
        logger.info("=" * 70)
        logger.info(f"Web URL: {args.web_url}")
        logger.info(f"Generating {len(test_cases)} fixture(s)...")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info("")

        download_dir = args.output_dir / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)

        fixtures_metadata = []
        failed_cases = []

        with WebFixtureGenerator(
            web_url=args.web_url,
            download_dir=download_dir,
            headless=not args.no_headless,
        ) as generator:
            for test_case in test_cases:
                test_name = test_case["name"]
                try:
                    metadata = generator.generate_fixture(test_case, args.output_dir)
                    if metadata:
                        fixtures_metadata.append(metadata)
                        logger.info(f"  ✓ {test_name}")
                    else:
                        failed_cases.append(
                            {"name": test_name, "error": "Generation failed"}
                        )
                        logger.error(f"  ✗ {test_name}: Generation failed")
                except Exception as e:
                    logger.error(f"  ✗ {test_name}: {e}")
                    failed_cases.append({"name": test_name, "error": str(e)})

        # Create version file
        version_info = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "generation_method": "web_ui_playwright",
            "web_url": args.web_url,
            "total_fixtures": len(fixtures_metadata),
            "failed_fixtures": len(failed_cases),
            "fixtures": fixtures_metadata,
        }

        if failed_cases:
            version_info["failures"] = failed_cases

        # Save version files
        version_txt_path = args.output_dir / "FIXTURES_VERSION.txt"
        with open(version_txt_path, "w") as f:
            f.write("# Reference Fixture Version Information\n")
            f.write(f"# Generated: {version_info['generated_at']}\n")
            f.write("# Method: Web UI (Playwright automation)\n")
            f.write(f"# Web URL: {version_info['web_url']}\n")
            f.write(f"# Total fixtures: {version_info['total_fixtures']}\n")
            f.write(f"# Failed: {version_info['failed_fixtures']}\n")
            f.write("\n")
            f.write("# See FIXTURES_VERSION.json for full metadata\n")

        version_json_path = args.output_dir / "FIXTURES_VERSION.json"
        with open(version_json_path, "w") as f:
            json.dump(version_info, f, indent=2)

        # Print summary
        print("\n" + "=" * 70)
        print("WEB FIXTURE GENERATION COMPLETE")
        print("=" * 70)
        print(f"  Generated: {version_info['total_fixtures']}")
        print(f"  Failed: {version_info['failed_fixtures']}")
        print("  Method: Web UI (Playwright)")
        print(f"  Web URL: {version_info['web_url']}")
        print(f"  Output: {args.output_dir}")
        print("=" * 70)

        if version_info["failed_fixtures"] > 0:
            logger.warning("Some fixtures failed to generate")
            logger.info(
                "NOTE: Web UI selectors may need updating based on actual UI structure"
            )
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
