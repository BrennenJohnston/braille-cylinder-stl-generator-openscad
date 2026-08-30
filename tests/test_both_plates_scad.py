"""
Both-plates mode (BETA) - the side-by-side pair, rendered.

With ``render_both_plates = "On"`` one render builds Cylinder A (embossing
plate) at -X and Cylinder B (counter plate) at +X, centres one barrel diameter
plus ``pair_spacing_mm`` apart, so the barrel surfaces sit exactly the slider's
distance from each other (Brennen chose the barrel-based measure 2026-08-25).
``plate_type`` is ignored while the toggle is On; Off must stay byte-identical
to the single-plate render, which the phase commits proved by sha256.

Worth stating about why these assertions exist:

* **Exactly two bodies.** The whole point of the mode is one STL holding one
  complete pair - not one merged blob (spacing failed) and not three pieces
  (something came apart).
* **The gap follows the slider, measured from centroids.** Bounding boxes lie
  here: raised braille dots stand ~1 mm proud of A's barrel, so the visible
  bbox gap can read slightly under the slider value while the geometry is
  correct. Centre distance = diameter + spacing is the definition.
* **The gear size gate fires ONCE.** The assert is file-scope, so a refused
  size must produce one message, not one per body - and no STL.

Render tests skip when no OpenSCAD binary is available; the source guards run
everywhere, including the no-OpenSCAD CI job.

License: PolyForm Noncommercial 1.0.0
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_gear_rollers_scad import SIZE_MESSAGE, _load_roller, _render  # noqa: E402
from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

# Default barrel 30.8 mm + default gap 10 mm.
DEFAULT_CENTER_DISTANCE_MM = 40.8
CENTROID_TOL_MM = 0.3


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.fixture(scope="module")
def openscad_binary():
    """Same resolution as the gear render tests: the .com wrapper, driven directly."""
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the both-plates render tests")


def _center_distance_x(bodies):
    left, right = sorted(bodies, key=lambda body: body.centroid[0])
    return float(right.centroid[0] - left.centroid[0])


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("value", ["On", "on"])
def test_both_mode_renders_two_spaced_bodies(
    trimesh_module, openscad_binary, tmp_path, value
):
    """Two watertight bodies, centres diameter + gap apart, hint echoed."""
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, f"both_{value}", {"render_both_plates": value}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)

    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 2
    assert all(body.is_watertight for body in bodies)
    assert all(body.volume > 0 for body in bodies)

    assert _center_distance_x(bodies) == pytest.approx(
        DEFAULT_CENTER_DISTANCE_MM, abs=CENTROID_TOL_MM
    )

    # A (raised dots outward) left, B (recess grid) right: the counter plate
    # subtracts material, so at the same shell the right body weighs less.
    left, right = sorted(bodies, key=lambda body: body.centroid[0])
    assert left.volume > right.volume

    assert "Both plates: one STL containing Cylinder A" in output
    assert "plate_type is ignored" in output


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_pair_spacing_follows_the_slider(trimesh_module, openscad_binary, tmp_path):
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "both_20",
        {"render_both_plates": "On", "pair_spacing_mm": 20},
    )
    mesh = _load_roller(trimesh_module, stl_path, output)
    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 2
    assert _center_distance_x(bodies) == pytest.approx(50.8, abs=CENTROID_TOL_MM)


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_both_mode_with_gears_builds_two_full_rollers(
    trimesh_module, openscad_binary, tmp_path
):
    """Each body spans the full 72 mm roller: gears arrived on both cylinders."""
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "both_gears",
        {"render_both_plates": "On", "integrated_gears": "On"},
    )
    mesh = _load_roller(trimesh_module, stl_path, output)
    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 2
    for body in bodies:
        assert body.is_watertight
        assert body.bounds[0][2] == pytest.approx(-10.0, abs=0.001)
        assert body.bounds[1][2] == pytest.approx(62.0, abs=0.001)


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_both_mode_keeps_the_pair_hint_single(openscad_binary, tmp_path):
    """
    In double-sided mode the per-plate Cylinder A/B filename hint stands aside
    for the pair hint: one render, one suggested filename.
    """
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "both_ds",
        {"render_both_plates": "On", "double_sided": "On", "Back_Line_1": "⠁⠃⠉"},
    )
    assert stl_path.exists(), f"double-sided both-mode did not render:\n{output[:800]}"
    assert "Both plates: one STL containing Cylinder A" in output
    assert "Suggested export filename: Cylinder_Pair_" in output
    assert "this render is Cylinder" not in output


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_an_off_size_geared_pair_is_refused_once(openscad_binary, tmp_path):
    """The file-scope size gate fires exactly once for the pair, and no STL."""
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "both_refused",
        {
            "render_both_plates": "On",
            "integrated_gears": "On",
            "paper_thickness_preset": "Custom",
            "cylinder_diameter_mm": 40,
        },
    )
    assert "ERROR:" in output, f"the size assert did not fire:\n{output[:800]}"
    assert output.count(SIZE_MESSAGE) == 1
    assert not stl_path.exists()


# --- source guards: these run without OpenSCAD ------------------------------


def test_the_both_parameters_are_not_preset_owned():
    """
    Trap C3, same as the gear toggle: the presets silently override -D for the
    keys they own. Both new parameters must stay out of both tables.
    """
    presets = (PROJECT_ROOT / "presets.scad").read_text(encoding="utf-8")
    assert "render_both_plates" not in presets
    assert "pair_spacing_mm" not in presets
