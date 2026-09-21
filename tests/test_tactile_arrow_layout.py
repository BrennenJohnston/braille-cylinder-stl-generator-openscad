"""
Tactile arrow layout follows the paper-thickness preset (Brennen, 2026-09-20).

The "0.4mm" preset keeps one seam arrow per braille row; the "0.3mm" preset
places exactly three, at mid-height and 15 mm above and below it, whatever the
row count - so a blind user can tell the presets apart by touch (three
separated arrows against a chain of four touching ones) and a 0.3 mm cylinder
will not nest with a 0.4 mm one. "Custom" is an explicit choice in this
generator and keeps one arrow per row.

These tests render the canonical file and measure the STL; the fast source-only
guards live in ``tests/test_tactile_mode.py``. Verdicts come from the output
text and file existence, never from an exit code.

License: PolyForm Noncommercial 1.0.0
"""

import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

# Both paper-thickness presets set the barrel to 30.8 x 52 (presets.scad), and
# the model is translated up by half its height on the way out.
RADIUS = 15.4
HEIGHT = 52.0
PITCH = 15.0
ARROW_WIDTH = 4.0
ARROW_LENGTH = 10.0
RECESS_CLEARANCE = 0.2

# The web generator's copy of the pitch. Absent on CI, so the cross-check skips
# rather than failing for a reason unrelated to this repo.
WEB_GEOMETRY_SPEC = (
    PROJECT_ROOT.parent / "braille-cylinder-stl-generator" / "app" / "geometry_spec.py"
)


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.fixture(scope="module")
def openscad_binary():
    """The console wrapper, driven directly: one test asserts on a FAILED render."""
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the tactile arrow layout render tests")


def _render(binary, tmp_path, name, defines):
    """Render once. Returns (stl_path, combined stdout+stderr)."""
    stl_path = tmp_path / f"{name}.stl"
    command = [str(binary), "--hardwarnings", "--check-parameter-ranges=true"]
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(SCAD_FILE)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=600, cwd=PROJECT_ROOT
    )
    return stl_path, (result.stdout or "") + "\n" + (result.stderr or "")


def arrow_angle_deg(output, raised):
    """
    The plate's arrow angle: 180 on both plates, the seam-gap centre, which
    the render's NOTE states (a lead-in before column 0 was tried and reverted
    on 2026-09-21, web decision D-T6).
    """
    assert "NOTE: tactile arrow at 180 deg on both plates" in output, (
        f"no tactile arrow NOTE in the render output:\n{output[:800]}"
    )
    return 180.0


def _seam_column(trimesh_module, stl_path, output, raised):
    """
    (z, dtheta) of every vertex on the arrow column that stands proud of the
    shell (raised) or sits below it (recessed), z measured from mid-height and
    dtheta in degrees from the plate's arrow angle (arrow_angle_deg). The bore,
    the end faces, the braille dots (which never come within 8 deg of the
    arrow - the 5 mm clear zone) and the seam channel's floor (it shares this
    column since D-T6, 0.5 mm down; the recess floor is 0.7 mm down) are
    excluded.
    """
    import numpy as np

    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"

    centre = arrow_angle_deg(output, raised)
    v = trimesh_module.load(stl_path).vertices
    r = np.hypot(v[:, 0], v[:, 1])
    dtheta = (
        (np.degrees(np.arctan2(v[:, 1], v[:, 0])) - centre + 180.0) % 360.0
    ) - 180.0
    z = v[:, 2] - HEIGHT / 2.0
    band = (np.abs(dtheta) < 8.0) & (np.abs(z) < HEIGHT / 2.0 - 0.01)
    if raised:
        mask = band & (r > RADIUS + 0.05)
    else:
        groove_floor = np.abs(r - (RADIUS - 0.5)) < 0.03
        mask = band & (r < RADIUS - 0.05) & (r > RADIUS - 1.0) & ~groove_floor
    order = np.argsort(z[mask])
    return z[mask][order], dtheta[mask][order]


def _check_outlines(z, intervals, tol=0.3):
    """
    Every seam-column vertex lies inside one of the expected (low, high) axial
    intervals, and every interval is actually occupied out to both its ends.

    Vertex GAPS are useless for telling arrows apart: the mesh only has vertices
    where the arrow outline meets the 64-facet shell, so a single 10 mm arrow
    can have a 6 mm run with no vertex in it - wider than the 5 mm gap between
    the three_spaced arrows. The empty stretches between intervals are what
    prove the arrows are separate.
    """
    assert len(z) > 0, "no seam-column vertices at all"
    stray = [
        float(v)
        for v in z
        if not any(lo - tol <= v <= hi + tol for lo, hi in intervals)
    ]
    assert not stray, f"vertices outside every expected arrow outline: {stray[:10]}"
    for lo, hi in intervals:
        inside = z[(z >= lo - tol) & (z <= hi + tol)]
        assert len(inside) > 0, f"no arrow at all in {lo}..{hi}"
        assert float(inside.min()) == pytest.approx(lo, abs=tol), (
            lo,
            hi,
            float(inside.min()),
        )
        assert float(inside.max()) == pytest.approx(hi, abs=tol), (
            lo,
            hi,
            float(inside.max()),
        )


def _apex_points_up(z, dtheta, intervals):
    """The top of each arrow is a point, the bottom its 4 mm base (about 15 deg here)."""
    for lo, hi in intervals:
        top = dtheta[(z > hi - 0.5) & (z <= hi + 0.3)]
        base = dtheta[(z >= lo - 0.3) & (z < lo + 0.5)]
        top_spread = float(top.max() - top.min())
        base_spread = float(base.max() - base.min())
        assert top_spread < 3.0 < 10.0 < base_spread, (lo, hi, top_spread, base_spread)


def _base_params(**overrides):
    params = {
        "indicator_mode": "Tactile",
        "Line_1": "⠁",
        "Line_2": "",
    }
    params.update(overrides)
    return params


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize(
    "plate, raised",
    [("Embossing Plate", True), ("Counter Plate", False)],
    ids=["emboss", "counter"],
)
def test_the_03_preset_places_three_arrows_at_the_pitch(
    openscad_binary, trimesh_module, tmp_path, plate, raised
):
    """Three separated features at -15, 0 and +15 mm, on both plates, same heights."""
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        f"three_spaced_{'emboss' if raised else 'counter'}",
        _base_params(paper_thickness_preset="0.3mm", plate_type=plate),
    )
    z, dtheta = _seam_column(trimesh_module, stl_path, output, raised)

    # Three outlines centred on -15, 0 and +15, with nothing on the seam in the
    # two stretches between them. The recess is the arrow grown by
    # offset(delta = clearance), a MITERED offset: its base moves down by the
    # clearance, but its apex - a 22.6 deg point - moves up by
    # clearance / sin(half-angle), about 1.02 mm, so the recess runs from
    # -5.2 to +6.02 about its centre (3.8 mm of bare surface between recesses;
    # 5 mm between the raised arrows).
    if raised:
        below, above = ARROW_LENGTH / 2.0, ARROW_LENGTH / 2.0
    else:
        half_angle = math.atan2(ARROW_WIDTH / 2.0, ARROW_LENGTH)
        below = ARROW_LENGTH / 2.0 + RECESS_CLEARANCE
        above = ARROW_LENGTH / 2.0 + RECESS_CLEARANCE / math.sin(half_angle)
    intervals = [(c - below, c + above) for c in (-PITCH, 0.0, PITCH)]
    _check_outlines(z, intervals)
    if raised:
        _apex_points_up(z, dtheta, intervals)


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_the_04_preset_keeps_one_touching_arrow_per_row(
    openscad_binary, trimesh_module, tmp_path
):
    """The default is untouched: four 10 mm arrows on 10 mm rows, one continuous chain."""
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        "per_row_emboss",
        _base_params(paper_thickness_preset="0.4mm", plate_type="Embossing Plate"),
    )
    z, dtheta = _seam_column(trimesh_module, stl_path, output, raised=True)
    # Four 10 mm outlines on the 10 mm row pitch: each one's apex touches the
    # next one's base, a chain from -20 to +20 with no empty stretch in it.
    intervals = [
        (c - ARROW_LENGTH / 2.0, c + ARROW_LENGTH / 2.0)
        for c in (-15.0, -5.0, 5.0, 15.0)
    ]
    _check_outlines(z, intervals)
    # Only the topmost arrow has a free apex: lower down, each apex shares its
    # height with the next arrow's base, so the spread there is the base's.
    _apex_points_up(z, dtheta, intervals[-1:])


@pytest.mark.requires_openscad
def test_the_fit_assert_refuses_a_barrel_too_short_for_the_outer_arrows(
    openscad_binary, tmp_path
):
    """
    The presets lock the barrel at 52 mm, so the only way to push the outer
    arrows off the ends is to move the pitch itself: at 30 mm they need 70.4 mm.
    A rejection, not a warning, to match the web generator.
    """
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        "pitch_too_large",
        _base_params(
            paper_thickness_preset="0.3mm",
            plate_type="Embossing Plate",
            TACTILE_THREE_SPACED_PITCH=30,
        ),
    )
    assert "three tactile arrows need a taller cylinder" in output, output[:800]
    assert not stl_path.exists(), "the assert must stop the export"


def test_the_pitch_matches_the_web_generator():
    """One number in two repos: 15 mm here, TACTILE_THREE_SPACED_PITCH_MM there."""
    scad = SCAD_FILE.read_text(encoding="utf-8")
    here = re.search(r"^TACTILE_THREE_SPACED_PITCH = ([0-9.]+);", scad, re.MULTILINE)
    assert here, "TACTILE_THREE_SPACED_PITCH is not declared"
    assert float(here.group(1)) == PITCH

    if not WEB_GEOMETRY_SPEC.exists():
        pytest.skip("web repository checkout not found beside this one")
    web = WEB_GEOMETRY_SPEC.read_text(encoding="utf-8")
    there = re.search(r"^TACTILE_THREE_SPACED_PITCH_MM = ([0-9.]+)", web, re.MULTILINE)
    assert there, "the web generator no longer declares TACTILE_THREE_SPACED_PITCH_MM"
    assert float(there.group(1)) == float(here.group(1)), (
        "the arrow pitch has drifted between the OpenSCAD and web generators"
    )
