#!/usr/bin/env python3
"""
Validation Framework Setup Checker

Verifies that the validation framework is properly configured and all
required tools are available.

Usage:
    python scripts/validate_setup.py [--verbose]

License: PolyForm Noncommercial 1.0.0
"""

import argparse
import logging
import platform
import shutil
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python packages...")
    
    required_packages = [
        ("trimesh", "Mesh loading and analysis"),
        ("numpy", "Numerical computing"),
        ("scipy", "Scientific computing"),
        ("pytest", "Test framework"),
        ("yaml", "YAML parsing"),
        ("requests", "HTTP client"),
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package:15s} - {description}")
        except ImportError:
            print(f"  ✗ {package:15s} - {description} (MISSING)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("  Install with: pip install -r tests/requirements.txt")
        return False
    
    print("  ✓ All Python packages installed")
    return True


def check_openscad():
    """Check if OpenSCAD is available."""
    print("\n🔧 Checking OpenSCAD...")
    
    openscad_path = shutil.which("openscad")
    if openscad_path:
        print(f"  ✓ OpenSCAD found: {openscad_path}")
        
        # Try to get version
        import subprocess
        try:
            result = subprocess.run(
                ["openscad", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = (result.stdout or result.stderr).strip()
            print(f"    Version: {version}")
        except Exception as e:
            print(f"    Warning: Could not get version: {e}")
        
        return True
    else:
        print("  ✗ OpenSCAD not found in PATH")
        print("    Install from: https://openscad.org/downloads.html")
        print("    Or see: tests/tool_versions.yml")
        return False


def check_cloudcompare():
    """Check if CloudCompare is available (optional)."""
    print("\n☁️  Checking CloudCompare (optional)...")
    
    cloudcompare_path = shutil.which("CloudCompare")

    # Also check common default install locations (users often don't add to PATH)
    if not cloudcompare_path:
        system = platform.system()
        candidates = []
        if system == "Windows":
            candidates = [
                Path(r"C:\Program Files\CloudCompare\CloudCompare.exe"),
            ]
        elif system == "Darwin":
            candidates = [
                Path("/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"),
            ]
        elif system == "Linux":
            candidates = [
                Path("/snap/bin/cloudcompare"),
                Path("/usr/bin/cloudcompare"),
                Path("/usr/local/bin/cloudcompare"),
            ]

        for p in candidates:
            if p.exists():
                cloudcompare_path = str(p)
                break

    if cloudcompare_path:
        print(f"  ✓ CloudCompare found: {cloudcompare_path}")
        return True

    print("  ⚠ CloudCompare not found (optional)")
    print("    Numeric deviation checks will be skipped")
    print("    Install from: https://www.cloudcompare.org/")
    return None  # None = optional, not critical


def check_git_lfs():
    """Check if Git LFS is installed."""
    print("\n📁 Checking Git LFS...")
    
    git_lfs_path = shutil.which("git-lfs")
    if git_lfs_path:
        print(f"  ✓ Git LFS found: {git_lfs_path}")
        return True
    else:
        print("  ⚠ Git LFS not found")
        print("    Required for fixture files (*.stl)")
        print("    Install from: https://git-lfs.github.com/")
        return False


def check_config_files():
    """Check if configuration files exist."""
    print("\n⚙️  Checking configuration files...")
    
    config_files = [
        ("tests/parameter_mapping.json", "Parameter mapping", True),
        ("tests/compare_config.json", "Comparison config", True),
        ("tests/tool_versions.yml", "Tool versions", True),
        ("tests/fixtures/cross_platform/test_cases.json", "Test cases", True),
        ("tests/requirements.txt", "Python requirements", True),
        ("pytest.ini", "Pytest config", True),
    ]
    
    all_present = True
    for file_path, description, required in config_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"  ✓ {description:25s} ({file_path})")
        else:
            marker = "✗" if required else "⚠"
            print(f"  {marker} {description:25s} ({file_path}) - MISSING")
            if required:
                all_present = False
    
    return all_present


def check_source_files():
    """Check if test modules exist."""
    print("\n🐍 Checking test modules...")
    
    test_modules = [
        "tests/openscad_runner.py",
        "tests/mesh_comparison.py",
        "tests/conftest.py",
        "tests/validate_parameter_schema.py",
        "tests/cross_platform_validation.py",
        "scripts/regenerate_fixtures.py",
    ]
    
    all_present = True
    for module_path in test_modules:
        full_path = PROJECT_ROOT / module_path
        if full_path.exists():
            print(f"  ✓ {module_path}")
        else:
            print(f"  ✗ {module_path} - MISSING")
            all_present = False
    
    return all_present


def check_scad_file():
    """Check if OpenSCAD file exists."""
    print("\n📄 Checking OpenSCAD file...")
    
    scad_file = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
    if scad_file.exists():
        print(f"  ✓ OpenSCAD file found: {scad_file.name}")
        return True
    else:
        print(f"  ✗ OpenSCAD file not found: {scad_file.name}")
        return False


def check_fixtures():
    """Check fixture status."""
    print("\n🗂️  Checking test fixtures...")
    
    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures" / "cross_platform"
    
    if not fixtures_dir.exists():
        print("  ⚠ Fixtures directory not found")
        return False
    
    # Check version file
    version_file = fixtures_dir / "FIXTURES_VERSION.txt"
    if version_file.exists():
        print(f"  ✓ Version file exists")
        with open(version_file) as f:
            first_line = f.readline().strip()
            print(f"    {first_line}")
    else:
        print("  ⚠ No FIXTURES_VERSION.txt (fixtures not generated)")
    
    # Count test case directories
    test_case_dirs = [d for d in fixtures_dir.iterdir() if d.is_dir()]
    if test_case_dirs:
        print(f"  ℹ️ Found {len(test_case_dirs)} test case fixture(s)")
        
        # Check if they have reference.stl files
        with_stl = sum(1 for d in test_case_dirs if (d / "reference.stl").exists())
        print(f"    {with_stl} with reference.stl")
        
        if with_stl == 0:
            print("  ⚠ No reference STL files found")
            print("    Generate with: python scripts/regenerate_fixtures.py")
            return False
    else:
        print("  ⚠ No test case fixtures found")
        print("    Generate with: python scripts/regenerate_fixtures.py")
        return False
    
    return True


def print_next_steps(all_checks_passed, has_fixtures):
    """Print next steps based on check results."""
    print("\n" + "=" * 70)
    
    if all_checks_passed and has_fixtures:
        print("✅ SETUP COMPLETE - Ready to run validation tests!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Validate parameter schema:")
        print("     python tests/validate_parameter_schema.py")
        print("\n  2. Run validation tests:")
        print("     pytest tests/cross_platform_validation.py -v")
        print("\n  3. Run specific test:")
        print("     pytest tests/cross_platform_validation.py -k cylinder_rounded_emboss_indicators_on")
    
    elif all_checks_passed and not has_fixtures:
        print("⚠️  SETUP INCOMPLETE - Generate fixtures first")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Start the web generator (in separate terminal):")
        print("     cd ../braille-cylinder-stl-generator")
        print("     python app.py")
        print("\n  2. Generate reference fixtures:")
        print("     python scripts/regenerate_fixtures.py")
        print("\n  3. Run validation tests:")
        print("     pytest tests/cross_platform_validation.py -v")
    
    else:
        print("❌ SETUP FAILED - Fix issues above")
        print("=" * 70)
        print("\nCommon issues:")
        print("  - Missing Python packages: pip install -r tests/requirements.txt")
        print("  - OpenSCAD not found: See tests/tool_versions.yml for install help")
        print("  - Missing files: Ensure you're in the project root directory")
    
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check validation framework setup"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    
    print("=" * 70)
    print("STL VALIDATION FRAMEWORK - SETUP CHECKER")
    print("=" * 70)
    
    # Run all checks
    checks = {
        "Python packages": check_python_packages(),
        "OpenSCAD": check_openscad(),
        "CloudCompare": check_cloudcompare(),
        "Git LFS": check_git_lfs(),
        "Config files": check_config_files(),
        "Test modules": check_source_files(),
        "OpenSCAD file": check_scad_file(),
    }
    
    # Fixtures are checked separately (not required for initial setup)
    has_fixtures = check_fixtures()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for check_name, result in checks.items():
        if result is True:
            status = "✓ PASS"
        elif result is None:
            status = "⚠ OPTIONAL"
        else:
            status = "✗ FAIL"
        print(f"  {status:12s} {check_name}")
    
    # Determine overall status
    critical_checks = [
        v for v in checks.values() if v is not None and v is not True
    ]
    all_checks_passed = len(critical_checks) == 0
    
    # Print next steps
    print_next_steps(all_checks_passed, has_fixtures)
    
    # Exit code
    if all_checks_passed:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
