# STL Validation Framework - Test Suite

This directory contains the automated validation framework for comparing OpenSCAD-generated STL files against web generator reference STLs.

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r tests/requirements.txt

# Install OpenSCAD (required)
# Windows: Download from https://openscad.org/downloads.html
# Linux: sudo apt install openscad
# macOS: brew install openscad

# Install CloudCompare (optional, for numeric deviation checks)
# Windows: Download from https://www.cloudcompare.org/
# Linux: sudo snap install cloudcompare
# macOS: brew install cloudcompare

# Initialize Git LFS (for STL fixture files)
git lfs install
```

### 2. Validate Parameter Schema

Check that OpenSCAD parameters match the web API:

```bash
python tests/validate_parameter_schema.py
```

### 3. Generate Reference Fixtures

Generate golden STL files from the web API:

```bash
# Generate all fixtures
python scripts/regenerate_fixtures.py

# Generate specific test case
python scripts/regenerate_fixtures.py --test-case cylinder_rounded_emboss_indicators_on

# Dry run (show what would be generated)
python scripts/regenerate_fixtures.py --dry-run
```

### 4. Run Validation Tests

```bash
# Run all tests
pytest tests/cross_platform_validation.py

# Run high priority tests only
pytest tests/cross_platform_validation.py -m high_priority

# Run specific test case
pytest tests/cross_platform_validation.py::TestSTLValidation::test_stl_validation[cylinder_rounded_emboss_indicators_on]

# Run with verbose output
pytest tests/cross_platform_validation.py -v -s

# Run smoke tests (fast sanity checks)
pytest tests/cross_platform_validation.py::TestOpenSCADSmoke -v
```

## Directory Structure

```
tests/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── conftest.py                         # Pytest configuration and fixtures
├── pytest.ini                          # Pytest settings (in project root)
│
├── validate_parameter_schema.py        # UI schema validator
├── openscad_runner.py                  # OpenSCAD CLI wrapper
├── mesh_comparison.py                  # Mesh comparison module
├── cross_platform_validation.py        # Main test suite
│
├── parameter_mapping.json              # OpenSCAD ↔ Web API parameter mapping
├── compare_config.json                 # Comparison tolerances and settings
├── tool_versions.yml                   # Required tool versions
│
└── fixtures/
    └── cross_platform/
        ├── README.md                   # Fixture documentation
        ├── test_cases.json             # Test case definitions
        ├── FIXTURES_VERSION.txt        # Web generator version info
        ├── .gitattributes              # Git LFS tracking
        └── <test_case_name>/           # One directory per test case
            ├── params.json             # Input parameters
            ├── reference.stl           # Web-generated STL (Git LFS)
            ├── reference_meta.json     # Mesh properties
            └── openscad_output.stl     # OpenSCAD STL (generated during tests)
```

## Test Modules

### `validate_parameter_schema.py`

Validates that OpenSCAD customizer parameters match the web API schema.

**Checks:**
- All OpenSCAD parameters are mapped to web API parameters
- Default values match between platforms
- Parameter types are compatible
- Value ranges match (where applicable)
- Section/group labels align with web UI

**Usage:**
```bash
python tests/validate_parameter_schema.py
```

**Exit codes:**
- `0`: All checks passed
- `1`: Errors found (unmapped params, type mismatches, default mismatches)
- `2`: Warnings only (range mismatches, section misalignment)

### `openscad_runner.py`

Python wrapper for OpenSCAD CLI, enabling automated STL generation.

**Features:**
- Auto-detects OpenSCAD executable (cross-platform)
- Parameter substitution via `-D` flags or JSON parameter files
- Timeout handling
- Batch generation support

**Usage:**
```python
from openscad_runner import OpenSCADRunner

runner = OpenSCADRunner()
result = runner.generate_stl(
    scad_file="model.scad",
    output_file="output.stl",
    parameters={"Line_1": "⠓⠑⠇⠇⠕", "shape_type": "card"}
)
```

**CLI:**
```bash
python tests/openscad_runner.py input.scad output.stl -D Line_1="⠓⠊" -D shape_type=card
```

### `mesh_comparison.py`

Compares two STL mesh files using trimesh and optionally CloudCompare.

**Comparison Metrics:**
- **Volume**: Overall shape accuracy (tolerance: ±1%)
- **Surface Area**: Detail preservation (tolerance: ±0.5%)
- **Bounding Box**: Dimensional accuracy (tolerance: ±0.1mm)
- **Watertightness**: Must match (critical for 3D printing)
- **Face/Vertex Count**: Informational only
- **Numeric Surface Deviation**: Max point-to-surface distance (tolerance: ±0.05mm, requires CloudCompare)

**Usage:**
```python
from mesh_comparison import MeshComparator

comparator = MeshComparator()
result = comparator.compare(
    reference_stl="reference.stl",
    test_stl="test.stl",
    config=config_dict
)
```

**CLI:**
```bash
python tests/mesh_comparison.py reference.stl test.stl --config tests/compare_config.json
```

### `cross_platform_validation.py`

Main pytest test suite for cross-platform validation.

**Test Classes:**
- `TestSTLValidation`: Main validation tests (parametrized by test case)
- `TestOpenSCADSmoke`: Quick smoke tests for OpenSCAD runner
- `TestMeshComparisonSmoke`: Quick smoke tests for mesh comparison
- `TestParameterSchema`: Schema consistency tests
- `TestHighPriority`: High priority test cases only

**Markers:**
- `@pytest.mark.requires_openscad`: Skipped if OpenSCAD not available
- `@pytest.mark.requires_cloudcompare`: Skipped if CloudCompare not available
- `@pytest.mark.high_priority`: High priority test cases
- `@pytest.mark.slow`: Slow running tests

## Configuration Files

### `parameter_mapping.json`

Machine-readable mapping between OpenSCAD customizer variables and web API parameters.

**Purpose:**
- Source of truth for parameter names and types
- Used by fixture generator to convert parameters
- Used by schema validator to check consistency

### `compare_config.json`

Centralized tolerances and comparison settings.

**Sections:**
- `tolerances`: Numeric tolerances for each metric
- `required_checks`: Which checks are mandatory vs. informational
- `alignment`: ICP alignment settings
- `cloudcompare`: CloudCompare CLI settings
- `reporting`: Report format and content
- `performance`: Execution settings (timeouts, caching)

### `tool_versions.yml`

Required tool versions and installation instructions.

**Tools:**
- OpenSCAD (required)
- Python packages (trimesh, numpy, scipy, pytest, etc.)
- CloudCompare (optional)
- Git LFS (required for fixtures)

## Workflow

### Initial Setup (One-time)

1. Install dependencies (Python packages, OpenSCAD, Git LFS)
2. Validate parameter schema
3. Generate reference fixtures from web API
4. Commit fixtures to Git (with LFS)

### Regular Testing

1. Run validation tests
2. Review failures (if any)
3. Investigate differences (geometry changes, parameter drift, etc.)
4. Update fixtures if web generator improves

### Adding New Test Cases

1. Add test case definition to `tests/fixtures/cross_platform/test_cases.json`
2. Generate reference fixture: `python scripts/regenerate_fixtures.py --test-case <name>`
3. Run validation: `pytest tests/cross_platform_validation.py::TestSTLValidation::test_stl_validation[<name>]`
4. Commit fixture to Git

### Updating Reference Fixtures

Regenerate fixtures when:
- ✅ Web generator improves (bug fixes, better geometry)
- ✅ Adding new test cases
- ✅ Parameter defaults change in web generator
- ❌ DO NOT regenerate for unrelated web UI changes
- ❌ DO NOT regenerate during routine testing

```bash
# Regenerate all fixtures
python scripts/regenerate_fixtures.py

# Review changes
git status
git diff tests/fixtures/cross_platform/FIXTURES_VERSION.txt

# Commit
git add tests/fixtures/cross_platform/
git commit -m "Update reference fixtures from web generator"
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: STL Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # Fetch LFS files
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install OpenSCAD
        run: |
          sudo add-apt-repository -y ppa:openscad/releases
          sudo apt-get update
          sudo apt-get install -y openscad
      
      - name: Install Python dependencies
        run: pip install -r tests/requirements.txt
      
      - name: Validate parameter schema
        run: python tests/validate_parameter_schema.py
      
      - name: Run validation tests
        run: pytest tests/cross_platform_validation.py -v
```

## Troubleshooting

### "OpenSCAD not found"

- **Windows**: Install from https://openscad.org/downloads.html, add to PATH
- **Linux**: `sudo apt install openscad`
- **macOS**: `brew install openscad`
- Or set `OPENSCAD_PATH` environment variable

### "CloudCompare not found"

CloudCompare is optional. Tests will skip numeric deviation checks if not available.

To install:
- **Windows**: Download from https://www.cloudcompare.org/
- **Linux**: `sudo snap install cloudcompare`
- **macOS**: `brew install cloudcompare`

### "Reference fixture not found"

Generate fixtures first:
```bash
python scripts/regenerate_fixtures.py
```

### "Git LFS not initialized"

```bash
git lfs install
git lfs pull
```

### "STL validation failed"

1. Check OpenSCAD version: `openscad --version`
2. Review parameter mapping: `tests/parameter_mapping.json`
3. Check for OpenSCAD code changes affecting geometry
4. Run with verbose logging: `pytest -v -s tests/cross_platform_validation.py::test_<name>`
5. Review detailed JSON report in `test_results/`

## References

- **Web Generator**: https://braille-cylinder-stl-generator.vercel.app
- **Web Source**: https://github.com/BrennenJohnston/braille-cylinder-stl-generator
- **OpenSCAD**: https://openscad.org/
- **CloudCompare**: https://www.cloudcompare.org/
- **Git LFS**: https://git-lfs.github.com/
- **trimesh**: https://trimesh.org/

---

**Last Updated**: 2026-01-09  
**Framework Version**: 1.0.0
