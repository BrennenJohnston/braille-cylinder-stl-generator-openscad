# Cross-Platform Test Fixtures

This directory contains reference STL files and test case definitions for validating the OpenSCAD braille generator against the web-based generator.

## Directory Structure

```
cross_platform/
├── README.md                          # This file
├── test_cases.json                    # Test case definitions
├── FIXTURES_VERSION.txt               # Web generator version used to create fixtures
├── .gitattributes                     # Git LFS tracking for *.stl files
└── <test_case_name>/                  # One directory per test case
    ├── params.json                    # Input parameters
    ├── reference.stl                  # Web-generated STL (Git LFS)
    ├── reference_meta.json            # Mesh properties from web STL
    └── openscad_output.stl            # OpenSCAD-generated STL (generated during tests, not committed)
```

## Fixture Generation

### Initial Setup

1. **Install Git LFS** (if not already installed):
   ```bash
   # Windows (PowerShell with Chocolatey)
   choco install git-lfs
   
   # Linux
   sudo apt install git-lfs
   
   # macOS
   brew install git-lfs
   
   # Initialize Git LFS
   git lfs install
   ```

2. **Verify Git LFS tracking**:
   ```bash
   # Should show *.stl tracked by LFS
   git lfs track
   ```

### Generating Reference Fixtures

Reference STLs are generated from the web API and checked into git with Git LFS:

```bash
# Generate all reference fixtures from web API
python scripts/regenerate_fixtures.py

# Review changes
git status
git diff tests/fixtures/cross_platform/FIXTURES_VERSION.txt

# Commit fixtures
git add tests/fixtures/cross_platform/
git commit -m "Generate reference fixtures from web generator v1.2.3"
```

### When to Regenerate Fixtures

Regenerate fixtures when:
- ✅ **Web generator improves** (bug fixes, better geometry)
- ✅ **Adding new test cases** to `test_cases.json`
- ✅ **Parameter defaults change** in web generator
- ❌ **DO NOT regenerate** for unrelated web UI changes
- ❌ **DO NOT regenerate** during routine testing (use cached fixtures)

## Test Execution

Tests use **cached fixtures** from git (no network required):

```bash
# Run all cross-platform validation tests
pytest tests/cross_platform_validation.py

# Run specific test case
pytest tests/cross_platform_validation.py::test_card_rounded_emboss_basic

# Run with verbose output
pytest tests/cross_platform_validation.py -v

# Generate JSON report for CI
pytest tests/cross_platform_validation.py --json-report --json-report-file=reports/validation.json
```

## Test Case Format

Each test case in `test_cases.json` defines:

- **name**: Unique test case identifier (snake_case)
- **description**: Human-readable description
- **priority**: `high`, `medium`, or `low`
- **tags**: Searchable tags (shape type, dot style, etc.)
- **parameters**: Complete parameter set for both generators
- **expected_properties**: Approximate mesh properties (volume, area, etc.)

Example:
```json
{
  "name": "cylinder_rounded_emboss_indicators_on",
  "description": "Cylinder: Rounded dots, Embossing plate, Indicators ON",
  "priority": "high",
  "tags": ["cylinder", "rounded", "emboss", "indicators_on", "core_matrix"],
  "parameters": {
    "Line_1": "⠞⠑⠌",
    "shape_type": "cylinder",
    "plate_type": "positive",
    "combined_shape": "rounded",
    "indicator_shapes": "on",
    ...
  },
  "expected_properties": {
    "is_watertight": true
  }
}
```

## Fixture Versioning

The `FIXTURES_VERSION.txt` file records the web generator version used to create the current fixtures:

```
web_generator_commit: abc123def456
web_generator_version: 1.2.3
web_api_url: https://braille-cylinder-stl-generator.vercel.app
generated_date: 2026-01-08T10:30:00Z
python_script: scripts/regenerate_fixtures.py
```

This enables:
- Reproducibility (know which web version created fixtures)
- Version tracking (git history of fixture updates)
- Debugging (compare OpenSCAD against specific web version)

## Git LFS Usage

STL files are stored with Git LFS to avoid bloating the repository:

- **Tracked files**: `*.stl` (both reference and OpenSCAD outputs if committed)
- **Storage**: GitHub provides 1GB LFS storage on free tier (sufficient for ~100 test cases)
- **Bandwidth**: 1GB/month download (sufficient for typical CI usage)

### LFS Commands

```bash
# List LFS files
git lfs ls-files

# Fetch LFS files
git lfs pull

# Check LFS status
git lfs status

# See LFS storage usage
git lfs fetch --all
```

## Comparison Tolerances

Tolerances are defined in `tests/compare_config.json`:

| Property | Tolerance | Notes |
|----------|-----------|-------|
| Volume | ±1% | Start loose, tighten after data collection |
| Surface Area | ±0.5% | |
| Bounding Box | ±0.1mm | Per dimension |
| Watertightness | Must match | Critical for 3D printing |
| Max Surface Deviation | ±0.05mm | CloudCompare C2M (optional) |

## Troubleshooting

### "Git LFS not initialized"
```bash
git lfs install
```

### "This repository is over its data quota"
- GitHub free tier: 1GB storage, 1GB/month bandwidth
- Solution: Clean up old fixtures or upgrade to larger plan
- Check usage: Repository Settings → Billing → Git LFS Data

### "Fixtures out of date"
- Check `FIXTURES_VERSION.txt` vs. current web version
- Regenerate if web generator has updates: `python scripts/regenerate_fixtures.py`

### "OpenSCAD output doesn't match"
1. Check OpenSCAD version: `openscad --version` (should be 2026.01.03+ with Manifold backend).  
   - Use **Development Snapshot / Nightly** builds with the **Manifold** geometry engine for faster rendering and consistent results.
2. Review parameter mapping: `tests/parameter_mapping.json`
3. Check for OpenSCAD code changes affecting geometry
4. Run with verbose logging: `pytest -v -s tests/cross_platform_validation.py::test_<name>`

## References

- **Web Generator**: https://braille-cylinder-stl-generator.vercel.app
- **Web Source**: https://github.com/BrennenJohnston/braille-cylinder-stl-generator
- **OpenSCAD Source**: https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad
- **Git LFS**: https://git-lfs.github.com/

---

**Last Updated**: 2026-01-09  
**Fixture Version**: Generated with OpenSCAD 2026.01.03 (Manifold backend)
