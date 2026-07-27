"""
Pytest configuration and fixtures for cross-platform STL validation.

This module provides:
- Tool version checking
- Shared fixtures for test cases
- Configuration loading
- Test environment setup

License: PolyForm Noncommercial 1.0.0
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Add project root to path. These imports must come after the sys.path insert,
# so E402 is expected here.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.mesh_comparison import MeshComparator  # noqa: E402
from tests.openscad_runner import OpenSCADRunner  # noqa: E402

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "requires_cloudcompare: mark test as requiring CloudCompare CLI",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (> 10s execution time)",
    )
    config.addinivalue_line(
        "markers",
        "cylinder: mark test as testing cylinder shape",
    )
    config.addinivalue_line(
        "markers",
        "emboss: mark test as testing embossing plate",
    )
    config.addinivalue_line(
        "markers",
        "counter: mark test as testing counter plate",
    )
    config.addinivalue_line(
        "markers",
        "basic: mark test as basic/fundamental test case",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        if "cylinder" in item.nodeid.lower():
            item.add_marker(pytest.mark.cylinder)
        if "emboss" in item.nodeid.lower():
            item.add_marker(pytest.mark.emboss)
        if "counter" in item.nodeid.lower():
            item.add_marker(pytest.mark.counter)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def tests_dir(project_root) -> Path:
    """Tests directory."""
    return project_root / "tests"


@pytest.fixture(scope="session")
def fixtures_dir(tests_dir) -> Path:
    """Cross-platform fixtures directory."""
    return tests_dir / "fixtures" / "cross_platform"


@pytest.fixture(scope="session")
def scad_file(project_root) -> Path:
    """Path to main OpenSCAD file."""
    scad_path = project_root / "Braille_Cylinder_STL_Generator.scad"
    if not scad_path.exists():
        pytest.skip(f"OpenSCAD file not found: {scad_path}")
    return scad_path


@pytest.fixture(scope="session")
def tool_versions(tests_dir) -> Dict[str, Any]:
    """Load tool versions configuration."""
    tool_versions_path = tests_dir / "tool_versions.yml"
    with open(tool_versions_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def comparison_config(tests_dir, pytestconfig) -> Dict[str, Any]:
    """Load comparison configuration."""
    import os
    
    # Check for custom config path (CLI option or environment variable)
    custom_config = pytestconfig.getoption("--comparison-config", None)
    if not custom_config:
        custom_config = os.environ.get("COMPARISON_CONFIG", None)
    
    if custom_config:
        config_path = Path(custom_config)
        logger.info(f"Using custom comparison config: {config_path}")
    else:
        config_path = tests_dir / "compare_config.json"
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Log which profile is being used
    profile = config.get("profile", "baseline")
    logger.info(f"Comparison profile: {profile}")

    # Allow CLI flag to disable CloudCompare usage even if installed
    if pytestconfig.getoption("--skip-cloudcompare"):
        config.setdefault("cloudcompare", {})["enabled"] = False

    return config


@pytest.fixture(scope="session")
def parameter_mapping(tests_dir) -> Dict[str, Any]:
    """Load parameter mapping."""
    mapping_path = tests_dir / "parameter_mapping.json"
    with open(mapping_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def test_cases(fixtures_dir) -> Dict[str, Any]:
    """Load test cases definitions."""
    test_cases_path = fixtures_dir / "test_cases.json"
    with open(test_cases_path, encoding="utf-8") as f:
        data = json.load(f)
    
    # CI GUARD: Fail fast if any card test cases are found
    # Card tests are disabled until web UI parity is restored
    for test_case in data.get("test_cases", []):
        shape_type = test_case.get("parameters", {}).get("shape_type", "")
        if shape_type == "card":
            pytest.fail(
                f"BLOCKED: Card test case '{test_case['name']}' found in test_cases.json. "
                f"Card tests are disabled until web UI parity is restored. "
                f"Only 'cylinder' shape_type is allowed."
            )
    
    return data


@pytest.fixture(scope="session")
def openscad_runner(tool_versions) -> OpenSCADRunner:
    """
    Create OpenSCAD runner instance.

    Skips all tests if OpenSCAD is not available.
    In CI mode (CI=true env var), enforces exact version and Manifold backend.
    """
    import os
    
    try:
        # Check if running in CI mode
        is_ci = os.environ.get("CI", "").lower() in ("true", "1", "yes")
        
        # Get version requirements from tool_versions.yml
        openscad_config = tool_versions.get("required_tools", {}).get("openscad", {})
        required_version = openscad_config.get("ci_version") if is_ci else None
        
        # Create runner with optional version enforcement
        runner = OpenSCADRunner(
            enforce_version=required_version if is_ci else None
        )
        
        version = runner.get_version()
        logger.info(f"OpenSCAD available: {version}")
        
        # Check Manifold backend (require in CI, warn in local)
        if is_ci:
            runner.check_manifold_backend(require_manifold=True)
            logger.info("✓ Manifold backend verified (CI mode)")
        elif not runner.use_manifold:
            logger.warning(
                "⚠ Manifold backend not available - results may differ from CI. "
                "Consider upgrading to OpenSCAD 2026.01.03+ nightly."
            )
        
        return runner
    except Exception as e:
        pytest.skip(f"OpenSCAD not available: {e}")


@pytest.fixture(scope="session")
def mesh_comparator(comparison_config) -> MeshComparator:
    """Create mesh comparator instance."""
    return MeshComparator(comparison_config)


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "stl_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def test_case_data(request, test_cases, fixtures_dir):
    """
    Parametrized fixture for individual test cases.

    Usage in test:
        @pytest.mark.parametrize("test_case_data", ["cylinder_rounded_emboss_indicators_on"], indirect=True)
        def test_something(test_case_data):
            test_name, params, expected_props, fixture_dir = test_case_data
    """
    test_case_name = request.param

    # Find test case in test_cases.json
    test_case = None
    for tc in test_cases["test_cases"]:
        if tc["name"] == test_case_name:
            test_case = tc
            break

    if not test_case:
        pytest.fail(f"Test case not found: {test_case_name}")

    # Get fixture directory
    fixture_dir = fixtures_dir / test_case_name

    return (
        test_case["name"],
        test_case["parameters"],
        test_case.get("expected_properties", {}),
        fixture_dir,
    )


# NOTE: a stub `check_tool_version()` helper used to live here. It was never
# called, and real OpenSCAD version enforcement is implemented in
# OpenSCADRunner._enforce_version() (see tests/openscad_runner.py), which is
# wired up by the `openscad_runner` fixture below whenever the `CI` env var
# is truthy. If you need to enforce another tool's version, add it there
# rather than reviving a parallel helper here.


@pytest.fixture(scope="session", autouse=True)
def check_environment(openscad_runner, mesh_comparator):
    """
    Check test environment before running tests.

    This fixture runs automatically at session start.
    """
    logger.info("=" * 70)
    logger.info("Cross-Platform STL Validation Framework")
    logger.info("=" * 70)

    # Check OpenSCAD
    openscad_version = openscad_runner.get_version()
    logger.info(f"✓ OpenSCAD: {openscad_version}")

    # Check CloudCompare (optional)
    if mesh_comparator.cloudcompare_path:
        logger.info(f"✓ CloudCompare: {mesh_comparator.cloudcompare_path}")
    else:
        logger.warning(
            "⚠ CloudCompare not found - numeric deviation checks will be skipped"
        )

    # Check Python packages
    import numpy
    import scipy
    import trimesh

    logger.info(f"✓ trimesh: {trimesh.__version__}")
    logger.info(f"✓ numpy: {numpy.__version__}")
    logger.info(f"✓ scipy: {scipy.__version__}")

    logger.info("=" * 70)


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--regenerate-fixtures",
        action="store_true",
        default=False,
        help="Regenerate reference fixtures before running tests",
    )
    parser.addoption(
        "--skip-cloudcompare",
        action="store_true",
        default=False,
        help="Skip CloudCompare numeric deviation checks",
    )
    parser.addoption(
        "--update-expected",
        action="store_true",
        default=False,
        help="Update expected properties in test_cases.json from test results",
    )
    parser.addoption(
        "--comparison-config",
        action="store",
        default=None,
        help="Path to comparison config JSON (default: tests/compare_config.json, strict: tests/compare_config_strict.json)",
    )
