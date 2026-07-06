from pathlib import Path


def test_indicator_shapes_not_cylinders_in_scad_source():
    """
    Lightweight regression guard:
    The indicator bug was caused by cylindrical markers in the OpenSCAD generator.

    This test intentionally checks the *source* (not geometry) so CI can fail fast
    even before OpenSCAD/mesh comparison runs.
    """

    scad_path = Path(__file__).resolve().parents[1] / "Braille_Cylinder_STL_Generator.scad"
    scad = scad_path.read_text(encoding="utf-8")

    # Modules required by the web-spec indicator implementation
    assert "module indicator_triangle_2d" in scad
    assert "module indicator_rectangle_2d" in scad
    assert "module place_cylinder_marker" in scad

    # Cylinder indicator usage must reference the triangle/rectangle modules
    assert "indicator_triangle_prism_centered" in scad
    assert "indicator_rectangle_prism_centered" in scad

    # The emboss/counter plates must share ONE per-row indicator module so the
    # counter renders as an exact mirror of the emboss layout (true mirrored
    # pair: identical triangle->rectangle spacing, opposite triangle direction).
    assert "module place_row_indicators" in scad

    # The shared module sets the global triangle direction via a single
    # rotate_180 flag (emboss apex right / counter apex left, verified by render).
    assert "indicator_triangle_prism_centered(tri_depth, rotate_180 = true)" in scad

    # Emboss renders the shared layout directly; the counter renders the SAME
    # module under mirror([0,1,0]) for the mirrored pair.
    assert "place_row_indicators(y_pos, INDICATOR_TRIANGLE_DEPTH_EMBOSS, INDICATOR_RECT_DEPTH_EMBOSS)" in scad
    assert "mirror([0, 1, 0])" in scad
    assert "place_row_indicators(y_pos, active_counter_height, active_counter_height)" in scad

    # Old buggy implementation patterns (cylindrical markers) must not reappear
    assert "active_emboss_base_diameter / 3" not in scad
    assert "Start marker" not in scad  # old marker terminology (start/end cylinders) should be gone
