"""
Tactile Indicator Mode Source Guards

`indicator_mode = "Tactile"` swaps the per-row recessed marker columns for a
single raised arrow (emboss) / matching recess (counter) centred in the seam
gap. These are fast source-only checks — like
``tests/test_indicator_source_guards.py`` they run in CI even where OpenSCAD
isn't installed, and they fail before the slow render/mesh comparison does.

They cover the three things most likely to silently break the feature:

1. The Customizer surface (dropdown + the five tactile sliders, in both the
   canonical desktop build and the MakerWorld single-file build).
2. The geometry invariants the nesting fit depends on — the 180 deg placement,
   the curvature-conforming shell band, and the recess clearance offset.
3. The Visual code path staying gated behind ``!tactile_on`` so the default
   mode is untouched.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
MAKERWORLD = (
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad"
)

# The five Tactile-only sliders, with the exact `[min:step:max]` each ships with.
TACTILE_SLIDERS = {
    "tactile_indicator_width": ("4.0", "[2:0.1:10]"),
    "tactile_indicator_length": ("10.0", "[2:0.1:15]"),
    "tactile_indicator_raise": ("0.5", "[0:0.1:2]"),
    "tactile_recess_clearance": ("0.2", "[0:0.05:1]"),
    "tactile_recess_extra_depth": ("0.2", "[0:0.05:1]"),
}

# 2026-08-18: the canonical defaults were aligned to the web app (length
# 5.0 -> 10.0 mm, raise 0.8 -> 0.5 mm). The MakerWorld build is re-flattened by
# its own phase and still carries the old pair, so the gap is pinned here rather
# than left to make the guard quietly wrong. Delete these two entries in the same
# change that re-flattens the variant.
MAKERWORLD_PENDING_REFLATTEN = {
    "tactile_indicator_length": "5.0",
    "tactile_indicator_raise": "0.8",
}

# How many braille-cell walks read the shared column-shift expression. Two plate
# modules, plus - in the canonical file since the double-sided phase -
# ds_back_recesses(), which walks the back text through the same expression so
# the back layout cannot drift from the front. The MakerWorld build is
# re-flattened in its own phase and still carries only the two. Raise its entry
# to match the canonical one in the same change that re-flattens the variant.
COLUMN_SHIFT_WALKS = {CANONICAL: 3, MAKERWORLD: 2}

BOTH_BUILDS = pytest.mark.parametrize(
    "scad_path", [CANONICAL, MAKERWORLD], ids=["canonical", "makerworld"]
)


def _read(path):
    assert path.exists(), f"SCAD file missing: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Customizer surface
# ---------------------------------------------------------------------------


@BOTH_BUILDS
def test_indicator_mode_dropdown(scad_path):
    """Default must be Visual, and must exactly match a dropdown option.

    (A default that doesn't match an option renders as a duplicate entry in
    OpenSCAD's Customizer — see tests/test_openscad_customizer.py.)
    """
    scad = _read(scad_path)
    assert 'indicator_mode = "Visual"; // [Visual, Tactile]' in scad, (
        "Expected the Indicator Mode dropdown declared as "
        '`indicator_mode = "Visual"; // [Visual, Tactile]`. Visual is the '
        "default so existing models keep rendering unchanged."
    )
    assert "/* [Indicator Mode] */" in scad, (
        "Expected the tactile parameters grouped under their own "
        "`/* [Indicator Mode] */` Customizer section."
    )


@BOTH_BUILDS
@pytest.mark.parametrize("name", sorted(TACTILE_SLIDERS))
def test_tactile_slider_declared(scad_path, name):
    """Each tactile slider keeps its documented default and range."""
    default, rng = TACTILE_SLIDERS[name]
    if scad_path == MAKERWORLD and name in MAKERWORLD_PENDING_REFLATTEN:
        default = MAKERWORLD_PENDING_REFLATTEN[name]
    scad = _read(scad_path)
    expected = f"{name} = {default}; // {rng}"
    assert expected in scad, (
        f"Expected `{expected}` in {scad_path.name}. Defaults and ranges are "
        f"mirrored in tests/parameter_mapping.json, which "
        f"tests/validate_parameter_schema.py cross-checks."
    )


def test_raise_stays_below_the_braille_dot_height():
    """The indicator must not out-stand the dots.

    Crush safety: the braille dots have to carry the rolling pressure, so the
    arrow's default raise is deliberately lower than the default rounded dot
    height (base 0.5 + dome 0.5 = 1.0 mm).
    """
    scad = _read(CANONICAL)

    def default_of(name):
        m = re.search(rf"^{re.escape(name)}\s*=\s*([0-9.]+)\s*;", scad, re.MULTILINE)
        assert m, f"Could not find default for `{name}`"
        return float(m.group(1))

    dot_height = default_of("rounded_dot_base_height") + default_of(
        "rounded_dot_dome_height"
    )
    raise_mm = default_of("tactile_indicator_raise")
    assert raise_mm < dot_height, (
        f"tactile_indicator_raise ({raise_mm} mm) must stay below the rounded "
        f"dot height ({dot_height} mm) so the dots, not the indicator, carry "
        f"the rolling pressure."
    )


# ---------------------------------------------------------------------------
# Geometry invariants
# ---------------------------------------------------------------------------


@BOTH_BUILDS
def test_tactile_modules_present(scad_path):
    scad = _read(scad_path)
    for module in (
        "module tactile_arrow_2d",
        "module tactile_shell_band",
        "module tactile_surface_prism",
        "module tactile_raised",
        "module tactile_recess_cut",
        "module tactile_gap_warning",
        "module tactile_rows_raised",
        "module tactile_rows_recessed",
    ):
        assert module in scad, f"Missing `{module}` in {scad_path.name}"


@BOTH_BUILDS
def test_arrow_apex_points_at_the_cylinder_top(scad_path):
    """Axial asymmetry is the whole point: the user feels which end is up.

    In the local frame of a place_cylinder_marker child, +X is circumferential
    and +Y is the cylinder top, so the apex vertex must be `[0, l/2]` and the
    two base vertices must sit at -l/2, symmetric in X.
    """
    scad = _read(scad_path)
    assert "polygon(points = [[-w/2, -l/2], [w/2, -l/2], [0, l/2]]);" in scad, (
        "Expected the arrow outline symmetric in X (so the mirrored counter "
        "recess has an identical outline) with its apex at +Y (the cylinder "
        "top, so a blind user can tell which end is up)."
    )


@BOTH_BUILDS
def test_indicator_sits_at_the_mirror_invariant_angle(scad_path):
    """180 deg is the fixed point of the counter plate's mirror/angle negation.

    Placing both the arrow and its recess there is what makes them self-align
    without any extra bookkeeping, so the literal angle is load-bearing.
    """
    scad = _read(scad_path)
    assert "place_cylinder_marker(180, y_pos, radius + span / 2, span, 0)" in scad, (
        "Expected the tactile prism placed at 180 deg (the seam-gap centre and "
        "the fixed point of the counter plate's mirror([0,1,0]) construction) "
        "with the child origin landing exactly on the shell surface."
    )


@BOTH_BUILDS
def test_curvature_conforming_band_uses_the_shell_tessellation(scad_path):
    """Raise and depth stay uniform only if band and shell tessellate alike.

    A flat 4 mm prism on a 15.4 mm radius loses ~0.13 mm at its edges to the
    chord sagitta — large next to the 0.2 mm nesting margin. Intersecting with
    a band built at CYLINDER_SHELL_FN removes that error.
    """
    scad = _read(scad_path)
    band = re.search(
        r"module tactile_shell_band\(r_in, r_out\)\s*\{.*?\n\}", scad, re.DOTALL
    )
    assert band, "Could not locate the `tactile_shell_band` module body"
    assert band.group(0).count("$fn = CYLINDER_SHELL_FN") == 2, (
        "Both cylinders in tactile_shell_band must use CYLINDER_SHELL_FN "
        "($fn TESSELLATION POLICY case 1) so the band is concentric with the "
        "shell and the radial raise/depth is constant across the arrow."
    )


@BOTH_BUILDS
def test_recess_is_grown_by_the_clearance_offset(scad_path):
    """The recess outline is the arrow outline grown uniformly in 2D."""
    scad = _read(scad_path)
    assert "offset(delta = tactile_recess_clearance)" in scad, (
        "The counter recess must apply `offset(delta = tactile_recess_clearance)` "
        "to the arrow outline so the raised arrow still enters when the two "
        "cylinders are slightly out of register."
    )
    assert (
        "tactile_shell_band(radius - tactile_indicator_raise - tactile_recess_extra_depth,"
        in scad
    ), (
        "The recess floor must be raise + extra_depth below the surface so the "
        "arrow bottoms out on clearance, not on the recess floor."
    )


@BOTH_BUILDS
def test_gap_warning_is_rendered_in_3d(scad_path):
    """MakerWorld's preview can't show console output, so warn in geometry."""
    scad = _read(scad_path)
    assert '"TACTILE GAP TOO SMALL: "' in scad
    assert "INVALID_TEXT_Z_OFFSET + 2 * INVALID_TEXT_STACK_GAP" in scad, (
        "The tactile warning should stack one step above TEXT TOO LONG, "
        "reusing the shared INVALID_TEXT_* placement constants."
    )
    assert "seam_gap_mm = PI * active_cylinder_diameter_mm - grid_width;" in scad


@BOTH_BUILDS
def test_constants_are_declared_before_the_values_that_use_them(scad_path):
    """OpenSCAD evaluates top-level assignments in source order.

    A constant referenced by a calculated value must already exist at that
    point, otherwise it silently resolves to `undef` and the seam-gap warning
    never fires. Guarding the ordering because the failure is invisible.
    """
    scad = _read(scad_path)
    decl = scad.index("TACTILE_MIN_GAP_MARGIN = ")
    use = scad.index("tactile_gap_too_small = ")
    assert decl < use, (
        "TACTILE_MIN_GAP_MARGIN must be declared before tactile_gap_too_small "
        "uses it — OpenSCAD assignments are sequential, so a forward reference "
        "evaluates to undef and the seam-gap warning silently never fires."
    )


# ---------------------------------------------------------------------------
# Visual mode must be untouched
# ---------------------------------------------------------------------------


@BOTH_BUILDS
def test_visual_marker_columns_are_gated_off_in_tactile_mode(scad_path):
    """Both plates skip the marker recesses when Tactile is selected."""
    scad = _read(scad_path)
    assert scad.count("if (!tactile_on) {") == 2, (
        "Expected exactly two `if (!tactile_on)` guards — one wrapping the "
        "emboss plate's place_row_indicators loop and one wrapping the counter "
        "plate's mirrored loop."
    )
    # The Visual implementation itself must survive untouched.
    assert "module place_row_indicators" in scad
    assert "mirror([0, 1, 0])" in scad


@BOTH_BUILDS
def test_column_shift_drops_the_marker_cells_in_tactile_mode(scad_path):
    """Text starts at column 0 in Tactile mode, and the grid stops widening."""
    scad = _read(scad_path)
    expected = COLUMN_SHIFT_WALKS[scad_path]
    assert (
        scad.count(
            "actual_col = tactile_on ? col :\n"
        )
        == expected
    ), (
        f"All {expected} braille-cell walks in {scad_path.name} must shift cells with "
        "`actual_col = tactile_on ? col : ...` so Tactile text starts at "
        "column 0 while Visual keeps its +1/+2 marker offset."
    )
    assert "actual_grid_columns = tactile_on ? active_grid_columns :" in scad, (
        "Tactile mode must not widen the grid with marker cells; the freed "
        "space is what makes the seam gap big enough for the indicator."
    )


def test_tactile_params_are_not_preset_driven():
    """Tactile sliders are slider-only, like grid_columns.

    The paper-thickness presets describe paper and dot geometry; the indicator
    is a mechanical alignment feature and must not move when the user switches
    preset.
    """
    presets = (PROJECT_ROOT / "presets.scad").read_text(encoding="utf-8")
    for name in list(TACTILE_SLIDERS) + ["indicator_mode"]:
        assert name not in presets, (
            f"`{name}` must not appear in presets.scad — tactile indicator "
            f"parameters are slider-only (same policy as grid_columns)."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
