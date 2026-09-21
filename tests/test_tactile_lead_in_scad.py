"""
The tactile arrow at the seam-gap centre and the seam channel down its column
(2026-09-21, web decision D-T6 after Brennen's test of the one-day lead-in) -
renders of both files. The file keeps its 2026-09-21 name: the lead-in it was
written for was reverted the same day, and the renders it makes are the same.

What this proves about the files the user actually renders:

  * the emboss plate's raised arrow and the counter plate's recess sit at
    180 degrees on both plates - the seam-gap centre, equal space either side
    of the arrow - and the render's NOTE says so;
  * the seam channel runs down the arrow column at 180, in two stretches that
    stop 0.3 mm short of the arrow chain: groove floor on both end caps and in
    the stretches, none across the chain, the stretch ends where the NOTE says
    (+/-20.3 mm about mid-height on the emboss plate at 13 cells; the counter
    plate's mitred recess apex reaches 1.02 mm further, so 21.32);
  * 14 cells render, with the card-fit NOTE and the red badge above the
    cylinder; 13 cells render with neither;
  * 15 cells keep the groove on the arrow column and trip the seam-gap
    warning, not the channel's;
  * the Version 2 file (54 mm barrel) places everything identically.

Judged by OUTPUT TEXT and FILE EXISTENCE, never by an exit code (the rule the
other render suites follow). Render tests skip without OpenSCAD.

License: PolyForm Noncommercial 1.0.0
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
V2_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"

RADIUS = 15.4
HEIGHT = {V1_FILE: 52.0, V2_FILE: 54.0}
ARROW_DEG = 180.0
FLOOR_R = RADIUS - 0.5
# The arrow chain at the defaults (four 10 mm arrows on 10 mm rows: -20..+20
# about mid-height) plus the 0.3 mm margin; the counter plate's recess base
# reaches the 0.2 mm clearance further and its mitred apex 0.2 / sin(11.31 deg).
EMBOSS_SPAN = (-20.3, 20.3)
COUNTER_SPAN = (-20.5, 21.3198)
CARD_NOTE = (
    "NOTE: this row needs 92.8 mm of card from the alignment arrow; the card is "
    "90 mm. Lower grid_columns to 13 or fewer."
)
S_C4 = "The seam channel was left out: the tactile arrows leave no room for it along the cylinder."


def _expected_stretches(height, span):
    end = height / 2.0 + 1.0  # the end face plus SEAM_CHANNEL_OVERSHOOT_MM
    return [[-end, span[0]], [span[1], end]]


def _flat(stretches):
    """pytest.approx takes no nested lists: [[a, b], [c, d]] -> [a, b, c, d]."""
    return [value for pair in stretches for value in pair]


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.fixture(scope="module")
def openscad_binary():
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the tactile seam-column render tests")


def _render(binary, tmp_path, scad_file, name, defines, hardwarnings=True):
    stl_path = tmp_path / f"{name}.stl"
    command = [str(binary), "--check-parameter-ranges=true"]
    if hardwarnings:
        command.insert(1, "--hardwarnings")
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(scad_file)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=600, cwd=PROJECT_ROOT
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    if hardwarnings:
        assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    return stl_path, output


def _noted_stretches(output):
    """(emboss, counter) stretches from the render's NOTE, as [[z_from, z_to], ...]."""
    match = re.search(
        r"NOTE: tactile arrow at 180 deg on both plates; seam channel stretches "
        r"(\[.*?\]) mm \(emboss\) / (\[.*?\]) mm \(counter\) about mid-height\.",
        output,
    )
    assert match, f"no tactile arrow NOTE:\n{output[:800]}"
    return json.loads(match.group(1)), json.loads(match.group(2))


def _feature_angles(trimesh_module, stl_path, height, raised, half_window_deg):
    """Angles of the arrow's own vertices: proud of the shell (raised) or below it (recess)."""
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    a = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
    near = np.abs(((a - ARROW_DEG + 180.0) % 360.0) - 180.0) < half_window_deg
    inside = (v[:, 2] > 1.0) & (v[:, 2] < height - 1.0)
    if raised:
        radial = r > RADIUS + 0.05
    else:
        # The groove floor shares the column (0.5 mm down); the recess floor
        # is 0.7 mm down, so a thin band separates the two.
        radial = (r < RADIUS - 0.05) & (r > RADIUS - 1.0) & (np.abs(r - FLOOR_R) > 0.03)
    return a[near & inside & radial]


def _groove_cap_angles(trimesh_module, stl_path, height):
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    caps = (np.abs(v[:, 2]) < 0.01) | (np.abs(v[:, 2] - height) < 0.01)
    floor = caps & (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03)
    return sorted(
        set(np.round(np.degrees(np.arctan2(v[floor, 1], v[floor, 0])) % 360.0, 2))
    )


def _groove_floor_z(trimesh_module, stl_path, height):
    """z (about mid-height) of every groove-floor vertex on the 180 deg column."""
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    a = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
    floor = (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03) & (np.abs(a - ARROW_DEG) < 0.5)
    return np.sort(v[floor, 2] - height / 2.0)


def _badge_vertices(trimesh_module, stl_path, height):
    """Vertices well above the top face: the red badge text (the Version 2 nub stops at +3 mm)."""
    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    return int((v[:, 2] > height + 4.0).sum())


def _assert_groove_in_the_stretches(trimesh_module, stl_path, height, span):
    """Floor on the caps and out to the stretch ends, nothing across the arrow chain."""
    assert _groove_cap_angles(trimesh_module, stl_path, height) == pytest.approx(
        [ARROW_DEG], abs=0.05
    )
    z = _groove_floor_z(trimesh_module, stl_path, height)
    assert len(z) > 0, "no groove floor on the arrow column"
    below, above = z[z < 0.0], z[z > 0.0]
    assert len(below) > 0 and len(above) > 0
    assert float(below.min()) == pytest.approx(-height / 2.0, abs=0.01)
    assert float(above.max()) == pytest.approx(height / 2.0, abs=0.01)
    # The stretches end exactly at the margin, and the chain between is bare.
    assert float(below.max()) == pytest.approx(span[0], abs=0.01)
    assert float(above.min()) == pytest.approx(span[1], abs=0.01)
    assert not ((z > span[0] + 0.02) & (z < span[1] - 0.02)).any(), (
        "groove floor under the arrow chain"
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("scad_file", [V1_FILE, V2_FILE], ids=["v1", "v2"])
def test_thirteen_cells_put_the_arrow_at_the_seam_centre_and_the_groove_down_its_column(
    openscad_binary, trimesh_module, tmp_path, scad_file
):
    """Arrow and recess at 180, groove at 180 in two stretches outside the chain, no card note."""
    import numpy as np

    height = HEIGHT[scad_file]
    emboss, out_e = _render(
        openscad_binary,
        tmp_path,
        scad_file,
        "emboss13",
        {"indicator_mode": "Tactile", "grid_columns": 13},
    )
    counter, out_c = _render(
        openscad_binary,
        tmp_path,
        scad_file,
        "counter13",
        {
            "indicator_mode": "Tactile",
            "grid_columns": 13,
            "plate_type": "Counter Plate",
        },
    )
    for output in (out_e, out_c):
        stretches_e, stretches_c = _noted_stretches(output)
        assert _flat(stretches_e) == pytest.approx(
            _flat(_expected_stretches(height, EMBOSS_SPAN)), abs=1e-4
        )
        assert _flat(stretches_c) == pytest.approx(
            _flat(_expected_stretches(height, COUNTER_SPAN)), abs=1e-4
        )
        assert "NOTE: this row needs" not in output
        assert "NOTE: The seam channel" not in output

    raised = _feature_angles(trimesh_module, emboss, height, True, 12.0)
    assert len(raised) > 0
    assert float(np.median(raised)) == pytest.approx(ARROW_DEG, abs=0.3)
    # The 4 mm arrow spans +/- 7.44 deg at this radius.
    assert raised.min() == pytest.approx(ARROW_DEG - 7.44, abs=0.3)
    assert raised.max() == pytest.approx(ARROW_DEG + 7.44, abs=0.3)

    recess = _feature_angles(trimesh_module, counter, height, False, 9.0)
    assert len(recess) > 0
    assert (recess.min() + recess.max()) / 2.0 == pytest.approx(ARROW_DEG, abs=0.3)

    _assert_groove_in_the_stretches(trimesh_module, emboss, height, EMBOSS_SPAN)
    _assert_groove_in_the_stretches(trimesh_module, counter, height, COUNTER_SPAN)
    assert _badge_vertices(trimesh_module, emboss, height) == 0
    assert _badge_vertices(trimesh_module, counter, height) == 0


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_fourteen_cells_render_with_the_card_note_and_badge(
    openscad_binary, trimesh_module, tmp_path
):
    """The cylinder holds 14; the 90 mm card does not, and the model says so - never a stop."""
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        V1_FILE,
        "emboss14",
        {"indicator_mode": "Tactile", "grid_columns": 14},
    )
    assert CARD_NOTE in output
    assert _badge_vertices(trimesh_module, stl_path, HEIGHT[V1_FILE]) > 0
    # The arrow column does not move with the cell count: the same stretches as at 13.
    stretches_e, _ = _noted_stretches(output)
    assert _flat(stretches_e) == pytest.approx(
        _flat(_expected_stretches(HEIGHT[V1_FILE], EMBOSS_SPAN)), abs=1e-4
    )
    _assert_groove_in_the_stretches(
        trimesh_module, stl_path, HEIGHT[V1_FILE], EMBOSS_SPAN
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_fifteen_cells_keep_the_groove_and_trip_the_gap_warning(
    openscad_binary, trimesh_module, tmp_path
):
    """15 cells: the arrow stays at 180 with its groove; the seam-GAP warning speaks, not the channel's."""
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        V1_FILE,
        "emboss15",
        {"indicator_mode": "Tactile", "grid_columns": 15},
        hardwarnings=False,
    )
    assert "Tactile indicator needs a seam gap of at least" in output
    assert "NOTE: The seam channel" not in output
    assert "NOTE: tactile arrow at 180 deg on both plates" in output
    _assert_groove_in_the_stretches(
        trimesh_module, stl_path, HEIGHT[V1_FILE], EMBOSS_SPAN
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_arrows_reaching_both_end_faces_leave_the_groove_out(
    openscad_binary, trimesh_module, tmp_path
):
    """
    A barrel only as tall as the chain plus the margins has no stretch of
    1 mm to spare: S-C4 in the console, the badge above the plate, no floor.
    The presets own the height, so the preset is Custom (its dot sizes differ,
    which is why only the omission is asserted here).
    """
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        V1_FILE,
        "emboss_short",
        {
            "indicator_mode": "Tactile",
            "grid_columns": 13,
            "paper_thickness_preset": "Custom",
            "cylinder_height_mm": 42,
        },
    )
    assert f"NOTE: {S_C4}" in output
    assert _groove_cap_angles(trimesh_module, stl_path, 42.0) == []
    assert _badge_vertices(trimesh_module, stl_path, 42.0) > 0
