"""
The tactile arrow at the seam-gap centre and the seam channel down its column,
the full height and through the raised arrows (2026-09-21, web decisions D-T6
and D-T7 after Brennen's prints) - renders of both files. The file keeps its
2026-09-21 name: the lead-in it was written for was reverted the same day,
and the renders it makes are the same.

What this proves about the files the user actually renders:

  * the emboss plate's raised arrow and the counter plate's recess sit at
    180 degrees on both plates - the seam-gap centre, equal space either side
    of the arrow - and the render's NOTE says so;
  * the seam channel runs down the arrow column at 180 the full height, on
    both plates: groove floor on both end caps and out to them;
  * on the emboss plate it is recut through the raised arrows over the span
    the NOTE states (the chain plus 0.3 mm at each end: +/-20.3 mm about
    mid-height at 13 cells on the default rows), so nothing stands proud of
    the surface on the centre line inside the chain - each arrow's point is
    gone - while the arrows' base corners, 7.4 degrees out, still do;
  * 14 cells render, with the card-fit NOTE and the red badge above the
    cylinder; 13 cells render with neither;
  * 15 cells keep the groove on the arrow column and trip the seam-gap
    warning, not the channel's;
  * a barrel no taller than the chain clamps the recut inside its end faces;
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
# about mid-height) plus the 0.3 mm margin at each end.
RECUT_SPAN = (-20.3, 20.3)
CARD_NOTE = (
    "NOTE: this row needs 92.8 mm of card from the alignment arrow; the card is "
    "90 mm. Lower grid_columns to 13 or fewer."
)


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


def _noted_recut(output):
    """The emboss plate's recut span from the render's NOTE, as [z_from, z_to]."""
    match = re.search(
        r"NOTE: tactile arrow at 180 deg on both plates; seam channel the full height, "
        r"recut through the raised arrows over z (\[.*?\]) mm about mid-height on the emboss plate\.",
        output,
    )
    assert match, f"no tactile arrow NOTE:\n{output[:800]}"
    return json.loads(match.group(1))


def _load(trimesh_module, stl_path):
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    a = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
    return v, r, a


def _recess_angles(trimesh_module, stl_path, height, half_window_deg):
    """Angles of the recess's own vertices: below the surface, off the groove floor band."""
    import numpy as np

    v, r, a = _load(trimesh_module, stl_path)
    near = np.abs(((a - ARROW_DEG + 180.0) % 360.0) - 180.0) < half_window_deg
    inside = (v[:, 2] > 1.0) & (v[:, 2] < height - 1.0)
    radial = (r < RADIUS - 0.05) & (r > RADIUS - 1.0) & (np.abs(r - FLOOR_R) > 0.03)
    return a[near & inside & radial]


def _groove_cap_angles(trimesh_module, stl_path, height):
    import numpy as np

    v, r, a = _load(trimesh_module, stl_path)
    caps = (np.abs(v[:, 2]) < 0.01) | (np.abs(v[:, 2] - height) < 0.01)
    floor = caps & (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03)
    return sorted(set(np.round(a[floor], 2)))


def _badge_vertices(trimesh_module, stl_path, height):
    """Vertices well above the top face: the red badge text (the Version 2 nub stops at +3 mm)."""
    v, _, _ = _load(trimesh_module, stl_path)
    return int((v[:, 2] > height + 4.0).sum())


def _assert_full_height_groove(trimesh_module, stl_path, height):
    """Floor on both caps at 180, and nowhere else."""
    import numpy as np

    assert _groove_cap_angles(trimesh_module, stl_path, height) == pytest.approx(
        [ARROW_DEG], abs=0.05
    )
    v, r, a = _load(trimesh_module, stl_path)
    # Within the barrel only: a red badge above the top face has vertices at
    # every radius.
    within = (v[:, 2] > -0.01) & (v[:, 2] < height + 0.01)
    floor = within & (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03)
    assert np.abs(a[floor] - ARROW_DEG).max() < 0.5, "groove floor off the arrow column"
    z = v[floor, 2]
    assert float(z.min()) == pytest.approx(0.0, abs=0.01)
    assert float(z.max()) == pytest.approx(height, abs=0.01)


def _assert_arrows_notched(trimesh_module, stl_path, height, span):
    """
    Nothing stands proud of the surface on the centre line inside the recut
    span (the points are gone); the arrows' base corners, 7.4 degrees out,
    still do.
    """
    import numpy as np

    v, r, a = _load(trimesh_module, stl_path)
    proud = r > RADIUS + 0.05
    off = np.abs(((a - ARROW_DEG + 180.0) % 360.0) - 180.0)
    z = v[:, 2] - height / 2.0
    inside = (z > span[0]) & (z < span[1])
    assert not (proud & inside & (off < 1.0)).any(), (
        "an arrow still stands on the centre line"
    )
    assert (proud & inside & (off > 6.0) & (off < 9.0)).any(), (
        "the arrows' base corners are gone"
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("scad_file", [V1_FILE, V2_FILE], ids=["v1", "v2"])
def test_thirteen_cells_put_the_arrow_at_the_seam_centre_and_the_groove_through_it(
    openscad_binary, trimesh_module, tmp_path, scad_file
):
    """Arrow and recess at 180, groove at 180 the full height, arrows notched, no card note."""
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
        assert _noted_recut(output) == pytest.approx(list(RECUT_SPAN), abs=1e-4)
        assert "NOTE: this row needs" not in output
        assert "NOTE: The seam channel" not in output

    _assert_full_height_groove(trimesh_module, emboss, height)
    _assert_full_height_groove(trimesh_module, counter, height)
    _assert_arrows_notched(trimesh_module, emboss, height, RECUT_SPAN)

    recess = _recess_angles(trimesh_module, counter, height, 9.0)
    assert len(recess) > 0
    assert (recess.min() + recess.max()) / 2.0 == pytest.approx(ARROW_DEG, abs=0.3)
    # The counter plate is untouched by the recut: its recess still spans its
    # full mitred width (4.4 mm at the surface, 4.5 at its floor - about 17.5
    # degrees measured on the floor vertices).
    assert 16.0 < recess.max() - recess.min() < 18.5

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
    # The arrow column does not move with the cell count: the same recut as at 13.
    assert _noted_recut(output) == pytest.approx(list(RECUT_SPAN), abs=1e-4)
    _assert_full_height_groove(trimesh_module, stl_path, HEIGHT[V1_FILE])
    _assert_arrows_notched(trimesh_module, stl_path, HEIGHT[V1_FILE], RECUT_SPAN)


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
    assert _noted_recut(output) == pytest.approx(list(RECUT_SPAN), abs=1e-4)
    _assert_full_height_groove(trimesh_module, stl_path, HEIGHT[V1_FILE])


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_a_barrel_no_taller_than_the_chain_clamps_the_recut_inside_its_faces(
    openscad_binary, trimesh_module, tmp_path
):
    """
    A 40 mm barrel: the chain plus its margins would reach past the end faces,
    so the recut stops 0.05 mm inside them (the first cut has the groove there
    already, and a gear face must never be nicked). The presets own the
    height, so the preset is Custom (its dot sizes differ, which is why only
    the span and the groove are asserted here).
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
            "cylinder_height_mm": 40,
        },
    )
    assert _noted_recut(output) == pytest.approx([-19.95, 19.95], abs=1e-4)
    _assert_full_height_groove(trimesh_module, stl_path, 40.0)
