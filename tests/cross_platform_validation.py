"""
Cross-Platform STL Validation Test Suite

Main test suite for validating OpenSCAD STL output against web generator reference.

This module contains pytest tests that:
1. Load test cases from fixtures
2. Generate STL with OpenSCAD
3. Compare against reference STL from web generator
4. Report results

License: PolyForm Noncommercial 1.0.0
"""

import json
import logging
from pathlib import Path

import pytest

from tests.mesh_comparison import ComparisonResult

logger = logging.getLogger(__name__)


class TestCrossPlatformValidation:
    """Cross-platform STL validation tests."""

    def test_environment_setup(self, openscad_runner, mesh_comparator, test_cases):
        """Verify test environment is properly configured."""
        assert openscad_runner is not None, "OpenSCAD runner not initialized"
        assert mesh_comparator is not None, "Mesh comparator not initialized"
        assert test_cases is not None, "Test cases not loaded"
        assert len(test_cases["test_cases"]) > 0, "No test cases defined"

        logger.info(f"Environment setup OK: {len(test_cases['test_cases'])} test cases")

    # Generate parametrized tests for each test case
    # NOTE: Only cylinder tests are active. Card tests removed until web UI parity restored.
    # 8 core matrix + 2 indicator isolation + 1 parametric + 1 multiline + 2 preset_03 = 14 total
    @pytest.mark.parametrize(
        "test_case_name",
        [
            # Core matrix: 8 combinations (dot shape × plate type × indicators)
            "cylinder_rounded_emboss_indicators_on",
            "cylinder_rounded_emboss_indicators_off",
            "cylinder_rounded_counter_indicators_on",
            "cylinder_rounded_counter_indicators_off",
            "cylinder_cone_emboss_indicators_on",
            "cylinder_cone_emboss_indicators_off",
            "cylinder_cone_counter_indicators_on",
            "cylinder_cone_counter_indicators_off",
            # Indicator isolation tests (minimal fixtures for bug diagnosis)
            "cylinder_indicator_recess_rounded",
            "cylinder_indicator_recess_cone",
            # Parametric variation test
            "cylinder_rounded_emboss_custom_cutout",
            # Multiline text fixture
            "cylinder_rounded_emboss_multiline",
            # 0.3 mm preset fixtures (PRESET_03 paper thickness)
            "cylinder_rounded_emboss_03mm",
            "cylinder_rounded_counter_03mm",
        ],
    )
    def test_stl_validation(
        self,
        test_case_name: str,
        scad_file: Path,
        openscad_runner,
        mesh_comparator,
        test_cases,
        fixtures_dir: Path,
        temp_output_dir: Path,
    ):
        """
        Validate OpenSCAD STL output against web generator reference.

        This test:
        1. Loads test case parameters
        2. Generates STL with OpenSCAD
        3. Loads reference STL from fixtures
        4. Compares meshes
        5. Reports results

        Args:
            test_case_name: Name of test case to run
            scad_file: Path to OpenSCAD file
            openscad_runner: OpenSCAD runner fixture
            mesh_comparator: Mesh comparator fixture
            test_cases: Test cases data
            fixtures_dir: Fixtures directory
            temp_output_dir: Temporary output directory
        """
        # Find test case
        test_case = None
        for tc in test_cases["test_cases"]:
            if tc["name"] == test_case_name:
                test_case = tc
                break

        assert test_case is not None, f"Test case not found: {test_case_name}"

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Test Case: {test_case_name}")
        logger.info(f"Description: {test_case['description']}")
        logger.info(f"Tags: {', '.join(test_case['tags'])}")
        logger.info(f"{'=' * 70}")

        # Get fixture directory
        fixture_dir = fixtures_dir / test_case_name
        reference_stl = fixture_dir / "reference.stl"

        # Check if reference fixture exists
        if not reference_stl.exists():
            pytest.skip(
                f"Reference fixture not found: {reference_stl}\n"
                f"Run: python scripts/regenerate_fixtures.py --test-case {test_case_name}"
            )

        # Generate OpenSCAD STL
        test_stl = temp_output_dir / f"{test_case_name}_openscad.stl"

        logger.info(f"Generating OpenSCAD STL: {test_stl.name}")
        result = openscad_runner.generate_stl(
            scad_file=scad_file,
            output_stl=test_stl,
            parameters=test_case["parameters"],
            timeout_seconds=300,
        )

        # Check OpenSCAD execution
        assert result.success, (
            f"OpenSCAD execution failed:\n"
            f"  Command: {result.command}\n"
            f"  Return code: {result.returncode}\n"
            f"  Stderr: {result.stderr}"
        )

        logger.info(f"✓ OpenSCAD completed in {result.duration_seconds:.1f}s")

        # Compare meshes
        logger.info(f"Comparing: {reference_stl.name} vs {test_stl.name}")
        comparison = mesh_comparator.compare(reference_stl, test_stl)

        # Log comparison results
        self._log_comparison_results(comparison)

        # Save detailed results
        results_file = temp_output_dir / f"{test_case_name}_results.json"
        self._save_results(
            test_case, comparison, result, reference_stl, test_stl, results_file
        )

        # Assert comparison passed
        if not comparison.passed:
            failure_msg = f"Mesh comparison failed for {test_case_name}:\n"
            for failure in comparison.failures:
                failure_msg += f"  - {failure}\n"
            failure_msg += f"\nDetailed results: {results_file}"
            pytest.fail(failure_msg)

        logger.info(f"✓ Test PASSED: {test_case_name}")

    def _log_comparison_results(self, comparison: ComparisonResult):
        """Log comparison results."""
        logger.info(f"  Volume diff: {comparison.volume_diff_percent:.2f}%")
        logger.info(f"  Surface area diff: {comparison.surface_area_diff_percent:.2f}%")
        logger.info(f"  Bounding box diff: {comparison.bounding_box_diff_mm:.3f} mm")
        logger.info(f"  Face count diff: {comparison.face_count_diff}")
        logger.info(f"  Vertex count diff: {comparison.vertex_count_diff}")
        logger.info(f"  Watertightness match: {comparison.watertightness_match}")

        if comparison.max_surface_deviation_mm is not None:
            logger.info(
                f"  Max surface deviation: {comparison.max_surface_deviation_mm:.3f} mm"
            )
        elif comparison.cloudcompare_available:
            logger.info("  Numeric deviation: Not computed (implementation pending)")
        else:
            logger.info("  Numeric deviation: Skipped (CloudCompare not available)")

    def _save_results(
        self,
        test_case: dict,
        comparison: ComparisonResult,
        openscad_result,
        reference_stl: Path,
        test_stl: Path,
        output_file: Path,
    ):
        """Save detailed test results to JSON."""
        results = {
            "test_case": {
                "name": test_case["name"],
                "description": test_case["description"],
                "tags": test_case["tags"],
                "parameters": test_case["parameters"],
            },
            "openscad_execution": {
                "success": openscad_result.success,
                "duration_seconds": openscad_result.duration_seconds,
                "command": openscad_result.command,
                "returncode": openscad_result.returncode,
            },
            "files": {
                "reference_stl": str(reference_stl),
                "test_stl": str(test_stl),
            },
            "comparison": comparison.to_dict(),
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)


# Convenience test groups for selective running


class TestEmbossPlates(TestCrossPlatformValidation):
    """Emboss plate tests only (faster, currently all passing)."""

    @pytest.mark.parametrize(
        "test_case_name",
        [
            "cylinder_rounded_emboss_indicators_on",
            "cylinder_rounded_emboss_indicators_off",
            "cylinder_cone_emboss_indicators_on",
            "cylinder_cone_emboss_indicators_off",
            "cylinder_rounded_emboss_custom_cutout",
            "cylinder_rounded_emboss_multiline",
            "cylinder_rounded_emboss_03mm",
        ],
    )
    def test_emboss_validation(
        self,
        test_case_name,
        scad_file,
        openscad_runner,
        mesh_comparator,
        test_cases,
        fixtures_dir,
        temp_output_dir,
    ):
        """Run emboss plate validation tests only."""
        self.test_stl_validation(
            test_case_name,
            scad_file,
            openscad_runner,
            mesh_comparator,
            test_cases,
            fixtures_dir,
            temp_output_dir,
        )


class TestCounterPlates(TestCrossPlatformValidation):
    """Counter plate tests only (known geometry issues with bowl recess)."""

    @pytest.mark.parametrize(
        "test_case_name",
        [
            "cylinder_rounded_counter_indicators_on",
            "cylinder_rounded_counter_indicators_off",
            "cylinder_cone_counter_indicators_on",
            "cylinder_cone_counter_indicators_off",
            "cylinder_rounded_counter_03mm",
        ],
    )
    def test_counter_validation(
        self,
        test_case_name,
        scad_file,
        openscad_runner,
        mesh_comparator,
        test_cases,
        fixtures_dir,
        temp_output_dir,
    ):
        """Run counter plate validation tests only."""
        self.test_stl_validation(
            test_case_name,
            scad_file,
            openscad_runner,
            mesh_comparator,
            test_cases,
            fixtures_dir,
            temp_output_dir,
        )


class TestIndicatorIsolation(TestCrossPlatformValidation):
    """Indicator recess isolation tests (for debugging indicator bugs)."""

    @pytest.mark.parametrize(
        "test_case_name",
        [
            "cylinder_indicator_recess_rounded",
            "cylinder_indicator_recess_cone",
        ],
    )
    def test_indicator_validation(
        self,
        test_case_name,
        scad_file,
        openscad_runner,
        mesh_comparator,
        test_cases,
        fixtures_dir,
        temp_output_dir,
    ):
        """Run indicator isolation validation tests."""
        self.test_stl_validation(
            test_case_name,
            scad_file,
            openscad_runner,
            mesh_comparator,
            test_cases,
            fixtures_dir,
            temp_output_dir,
        )


def main():
    """Run tests from command line."""
    import sys

    import pytest

    # Run pytest with this file
    exit_code = pytest.main([__file__, "-v"] + sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
