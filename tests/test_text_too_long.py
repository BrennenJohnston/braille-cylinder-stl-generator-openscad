"""
"TEXT TOO LONG" Warning Geometry Test

Phase 6c added a second warning extrusion on the emboss plate, parallel to
the existing "INVALID CHARACTERS" marker. It fires when any line's character
count exceeds the text capacity — i.e. ``active_grid_columns``. Text
capacity is always ``grid_columns``; when indicators are On the grid is
widened by 2 cells for the markers, so the text capacity is unchanged.
This test renders a deliberately oversized fixture and confirms the
warning shows up above the cylinder.

The test depends on:
  - the canonical SCAD file ``Braille_Cylinder_STL_Generator.scad``
  - a local OpenSCAD binary (prefers the nightly 2026.01.03 install if
    present at the canonical Windows path, then falls back to whatever
    ``OpenSCADRunner`` auto-detects). The render test is skipped if no
    OpenSCAD can be located — that's the expected outcome in the
    ``test-quick`` CI job, which intentionally has no OpenSCAD installed.
  - ``trimesh`` (already in tests/requirements.txt)

We render two STLs:
  1. A baseline with short lines (no warning expected).
  2. The same parameters but with ``Line_1`` oversized (warning expected).

Each STL is loaded via trimesh and the bounding-box Z-max is inspected.
The warning is centered at ``cylinder_height/2 + INVALID_TEXT_Z_OFFSET +
8 + INVALID_TEXT_DEPTH/2`` and is ``INVALID_TEXT_DEPTH`` (=2 mm) tall, so
the oversize render's Z-max must exceed the baseline by at least
``INVALID_TEXT_DEPTH`` mm. We use ``cylinder_height/2`` as the reference
because the SCAD positions the cylinder centered at z=0 and then
translates the whole emboss plate up by ``cylinder_height/2``, so the
cylinder top sits at ``cylinder_height``.

License: PolyForm Noncommercial 1.0.0
"""

import os
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

sys.path.insert(0, str(Path(__file__).parent))


def _resolve_openscad_path():
    """
    Prefer the nightly 2026.01.03 install on Windows when present
    (auto-detect in ``OpenSCADRunner`` ignores the nightly path). Fall
    back to ``OPENSCAD`` env var, then auto-detect.
    """
    nightly = Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.exe")
    if nightly.exists():
        return nightly
    env_path = os.environ.get("OPENSCAD")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    return None  # let OpenSCADRunner auto-detect

# Same braille glyph used by other fixtures; six dots so it always produces
# extrusion geometry on the cylinder surface.
BRAILLE_FULL_CELL = "\u283f"  # U+283F: braille pattern dots-123456


def _scad_constant(name, default=None):
    """Pull a numeric top-level constant out of the SCAD source."""
    text = SCAD_FILE.read_text(encoding="utf-8")
    m = re.search(rf"^\s*{re.escape(name)}\s*=\s*([0-9.+\-]+)\s*;", text, re.MULTILINE)
    if not m:
        if default is not None:
            return default
        raise AssertionError(f"Could not find constant `{name}` in SCAD source")
    raw = m.group(1)
    return float(raw) if "." in raw else int(raw)


def _baseline_params():
    """
    Parameters used for both render passes. Mirror the rounded-emboss
    fixture so OpenSCAD path is well-trodden; lines stay short enough that
    capacity (= grid_columns = 11, unchanged by indicators) is never
    exceeded.
    """
    return {
        "Line_1": BRAILLE_FULL_CELL * 3,
        "Line_2": "",
        "Line_3": "",
        "Line_4": "",
        "shape_type": "cylinder",
        "plate_type": "positive",
        "combined_shape": "rounded",
        "indicator_shapes": "on",
        "paper_thickness_preset": "Custom",
        "cylinder_diameter_mm": 30.75,
        "cylinder_height_mm": 52.0,
        "polygon_cutout_radius_mm": 13.0,
        "polygon_cutout_points": 12,
        "seam_offset_degrees": 0.0,
        "grid_columns": 11,
        "grid_rows": 4,
        "cell_spacing": 6.5,
        "line_spacing": 10.0,
        "dot_spacing": 2.5,
        "braille_y_adjust": 0.0,
        "rounded_dot_base_diameter": 2.0,
        "rounded_dot_base_height": 0.2,
        "rounded_dot_dome_diameter": 1.5,
        "rounded_dot_dome_height": 0.6,
        "bowl_counter_dot_base_diameter": 1.8,
        "counter_dot_depth": 0.8,
        "hemisphere_quality": "low",
        "cone_segments": 12,
    }


@pytest.fixture(scope="module")
def _trimesh():
    try:
        import trimesh
    except ImportError:
        pytest.skip("trimesh is not installed; skipping render-based warning test")
    return trimesh


@pytest.fixture(scope="module")
def warning_offsets():
    """Pull the warning-text positioning constants directly from the SCAD."""
    return {
        "z_offset": _scad_constant("INVALID_TEXT_Z_OFFSET"),
        "size": _scad_constant("INVALID_TEXT_SIZE"),
        "depth": _scad_constant("INVALID_TEXT_DEPTH"),
    }


@pytest.fixture(scope="module")
def warning_runner():
    """
    Module-scoped OpenSCAD runner that prefers the nightly install. Lives
    independently of the session-scoped ``openscad_runner`` fixture so the
    rest of the suite is unaffected.
    """
    from openscad_runner import OpenSCADNotFoundError, OpenSCADRunner

    explicit = _resolve_openscad_path()
    try:
        return OpenSCADRunner(openscad_path=explicit)
    except OpenSCADNotFoundError as exc:
        pytest.skip(f"OpenSCAD not available for render-based warning test: {exc}")


def _render(openscad_runner, tmp_path, params, name):
    """Render one STL with the given param dict; return the trimesh mesh."""
    stl_path = tmp_path / f"{name}.stl"
    result = openscad_runner.generate_stl(
        scad_file=SCAD_FILE,
        output_stl=stl_path,
        parameters=params,
        timeout_seconds=180,
    )
    assert result.success, (
        f"OpenSCAD failed to render `{name}` for TEXT TOO LONG test\n"
        f"returncode={result.returncode}\n"
        f"stderr (truncated): {result.stderr[:500]}"
    )
    return stl_path


def _z_max(trimesh_module, stl_path):
    """Return the bounding-box Z-max of an STL via trimesh."""
    mesh = trimesh_module.load(stl_path, force="mesh")
    return float(mesh.bounds[1][2])


@pytest.mark.slow
def test_text_too_long_emits_warning_extrusion(
    warning_runner, _trimesh, warning_offsets, tmp_path
):
    """
    Baseline render (short line, capacity not exceeded) must NOT emit the
    "TEXT TOO LONG" extrusion above the cylinder. The oversized render
    (Line_1 well over capacity) must emit it. We assert the difference in
    Z-max bounding box is at least INVALID_TEXT_DEPTH (2 mm).
    """
    baseline_params = _baseline_params()
    # Design A: text capacity is always grid_columns, unchanged by indicators.
    capacity = baseline_params["grid_columns"]  # indicators on => still 11

    # Oversized: well above capacity to be unambiguous (capacity 11 -> use 15).
    oversize_params = dict(baseline_params)
    oversize_params["Line_1"] = BRAILLE_FULL_CELL * (capacity + 4)

    # Regression guard: a line of EXACTLY grid_columns chars with indicators
    # On must NOT trigger the warning. This is the case that the old
    # Design-B threshold (grid_columns - 2) wrongly flagged.
    exact_params = dict(baseline_params)
    exact_params["Line_1"] = BRAILLE_FULL_CELL * capacity

    baseline_stl = _render(warning_runner, tmp_path, baseline_params, "baseline")
    oversize_stl = _render(warning_runner, tmp_path, oversize_params, "oversize")
    exact_stl = _render(warning_runner, tmp_path, exact_params, "exact")

    z_baseline = _z_max(_trimesh, baseline_stl)
    z_oversize = _z_max(_trimesh, oversize_stl)
    z_exact = _z_max(_trimesh, exact_stl)

    cyl_top = baseline_params["cylinder_height_mm"]  # cylinder centered then translated up
    z_offset = warning_offsets["z_offset"]
    depth = warning_offsets["depth"]

    # The TEXT TOO LONG warning is stacked at cyl_top + z_offset + 8 (centered),
    # so its top sits at cyl_top + z_offset + 8 + depth/2.
    expected_warning_top = cyl_top + z_offset + 8 + depth / 2

    # Baseline: nothing above cylinder top apart from embossed dots
    # (rounded_dot_base_height + rounded_dot_dome_height = 0.8 mm).
    assert z_baseline < cyl_top + 2.0, (
        f"Baseline render has unexpected geometry above the cylinder: "
        f"z_max={z_baseline:.3f}, cylinder_top={cyl_top:.3f}. The "
        f'"TEXT TOO LONG" warning should not fire for the baseline.'
    )

    # Exact capacity (grid_columns chars, indicators On): must NOT warn.
    # Under the old Design-B threshold this falsely fired — this is the
    # regression guard for that bug.
    assert z_exact < cyl_top + 2.0, (
        f"Exact-capacity render ({capacity} chars with indicators on) "
        f"unexpectedly emitted geometry above the cylinder: "
        f"z_max={z_exact:.3f}, cylinder_top={cyl_top:.3f}. Text capacity "
        f'is grid_columns, so the "TEXT TOO LONG" warning must NOT fire '
        f"at exactly grid_columns characters."
    )

    # Oversize: warning must clear the baseline by at least one warning depth.
    assert z_oversize >= z_baseline + depth, (
        f"Oversize render did not raise the bounding box by at least "
        f"INVALID_TEXT_DEPTH ({depth} mm). Got z_baseline={z_baseline:.3f}, "
        f"z_oversize={z_oversize:.3f}. The TEXT TOO LONG warning may have "
        f"failed to fire."
    )

    # And the warning's expected top must be within the oversize bounds.
    # Allow 1 mm slack for FP / float-extrude end-cap geometry.
    assert z_oversize >= expected_warning_top - 1.0, (
        f"Oversize render's z_max ({z_oversize:.3f}) is below the expected "
        f"warning top ({expected_warning_top:.3f} = cylinder_top {cyl_top} + "
        f"z_offset {z_offset} + 8 + depth/2 {depth/2}). Either the warning "
        f"didn't fire or the stack offset constant drifted."
    )


def test_warning_source_constants_present():
    """
    Cheap source-only guard: even when OpenSCAD isn't available (e.g. in
    the CI `test-quick` job), assert the SCAD still contains the literal
    "TEXT TOO LONG" warning, the stacked z-offset, and the named
    positioning constants this test depends on.
    """
    src = SCAD_FILE.read_text(encoding="utf-8")
    assert '"TEXT TOO LONG"' in src, "Expected literal `\"TEXT TOO LONG\"` in SCAD source"
    assert "INVALID_TEXT_Z_OFFSET + INVALID_TEXT_STACK_GAP" in src, (
        "Expected the TEXT TOO LONG warning to be stacked at "
        "INVALID_TEXT_Z_OFFSET + INVALID_TEXT_STACK_GAP (above the "
        "INVALID CHARACTERS marker). This is a structural invariant of "
        "the warning placement."
    )
    for const in (
        "INVALID_TEXT_Z_OFFSET",
        "INVALID_TEXT_SIZE",
        "INVALID_TEXT_DEPTH",
        "INVALID_TEXT_STACK_GAP",
    ):
        assert re.search(rf"^\s*{const}\s*=", src, re.MULTILINE), (
            f"Expected named constant `{const}` in SCAD source."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
