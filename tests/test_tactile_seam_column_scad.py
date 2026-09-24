"""
The tactile arrow at the seam-gap centre and the seam channel down its column
(2026-09-21, web decisions D-T6 and D-T7 after Brennen's prints), stepping
ROUND the raised arrows on the emboss plate since 2026-09-22 (web decision
D-T8: the cut through each arrow took its point and made the triangle less
distinguishable by touch) - renders of both files. The file keeps its
2026-09-21 name: the lead-in it was written for was reverted the same day.

What this proves about the files the user actually renders:

  * the emboss plate's raised arrow and the counter plate's recess sit at
    180 degrees on both plates - the seam-gap centre - and the render's NOTE
    says where the emboss plate's groove leaves and rejoins the column;
  * the counter plate's groove runs straight down the arrow column the full
    height; the emboss plate's is on the column at both end caps and off it,
    on the first-cell side (above 180 degrees), everywhere inside the arrow
    chain - never on the arrows' centre line;
  * every raised arrow is whole: its point still stands proud on the centre
    line, and so do its base corners, 7.4 degrees out;
  * the groove's floor IS the web generator's path (app/geometry_spec.py
    _tactile_detour_path, read from the sibling web checkout and skipped
    without it) - per-row and three-arrow layouts, gears off and on;
  * the three-arrow (0.3mm preset) layout returns to the column between arrows;
  * 14 cells render with the card-fit NOTE and badge; 13 with neither;
  * 15 cells leave the groove out on both plates and say why (S-C5), beside
    the seam-gap warning;
  * the Version 2 file (54 mm barrel) places everything identically.

Judged by OUTPUT TEXT and FILE EXISTENCE, never by an exit code (the rule the
other render suites follow). Render tests skip without OpenSCAD.

License: PolyForm Noncommercial 1.0.0
"""

import json
import math
import os
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
# The web generator, for the path parity test; absent on CI.
WEB_REPO = Path(
    os.environ.get(
        "BRAILLE_WEB_REPO", str(PROJECT_ROOT.parent / "braille-cylinder-stl-generator")
    )
)

RADIUS = 15.4
HEIGHT = {V1_FILE: 52.0, V2_FILE: 54.0}
ARROW_DEG = 180.0
FLOOR_R = RADIUS - 0.5
# Where the emboss plate's groove leaves and rejoins the column at the
# defaults (four 10 mm arrows on 10 mm rows, a chain from -20 to +20 about
# mid-height): 3.061 mm below the bottom base, 1.061 mm above the top tip.
DETOUR_SPAN = (-23.0607, 21.0607)
# How far it swings: 2.75 mm (tangent plane) at each base corner, 10.29
# degrees on the 15.4 mm barrel.
DETOUR_MAX_DEG = 190.292
# The arrow tips, about mid-height: each is 5 mm above its row centre.
TIPS = (20.0, 10.0, 0.0, -10.0)
CARD_NOTE = (
    "NOTE: this row needs 92.8 mm of card from the alignment arrow; the card is "
    "90 mm. Lower grid_columns to 13 or fewer."
)
# S-C5, the web generator's own words (signed off by Brennen 2026-09-23).
S_C5 = (
    "NOTE: The seam channel was left out: there is not enough room for it beside the "
    "alignment arrows. Reduce the number of braille cells, increase the cylinder "
    "diameter, or narrow the indicator."
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
    # One plate unless a test asks for the pair: the file's default renders both.
    defines = {"render_both_plates": "Off", **defines}
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


def _noted_detour(output):
    """The emboss plate's detour from the render's NOTE: ([z_from, z_to], widest degrees)."""
    match = re.search(
        r"NOTE: tactile arrow at 180 deg on both plates; seam channel the full height, round the raised "
        r"arrows on the emboss plate's first-cell side, off the column over z (\[.*?\]) mm about "
        r"mid-height and out to ([0-9.]+) deg\.",
        output,
    )
    assert match, f"no tactile arrow NOTE:\n{output[:800]}"
    return json.loads(match.group(1)), float(match.group(2))


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


def _floor(trimesh_module, stl_path, height, band=0.03):
    """(angle, z about mid-height) of the groove floor's vertices within the barrel."""
    v, r, a = _load(trimesh_module, stl_path)
    # Within the barrel only: a red badge above the top face has vertices at
    # every radius.
    within = (v[:, 2] > -0.01) & (v[:, 2] < height + 0.01)
    floor = within & (r > FLOOR_R - band) & (r < FLOOR_R + band)
    return a[floor], v[floor, 2] - height / 2.0


def _badge_vertices(trimesh_module, stl_path, height):
    """Vertices well above the top face: the red badge text (the Version 2 nub stops at +3 mm)."""
    v, _, _ = _load(trimesh_module, stl_path)
    return int((v[:, 2] > height + 4.0).sum())


def _assert_straight_groove(trimesh_module, stl_path, height):
    """The counter plate: floor on both caps at 180, and nowhere else."""
    import numpy as np

    assert _groove_cap_angles(trimesh_module, stl_path, height) == pytest.approx(
        [ARROW_DEG], abs=0.05
    )
    angles, z = _floor(trimesh_module, stl_path, height)
    assert np.abs(angles - ARROW_DEG).max() < 0.5, "groove floor off the arrow column"
    assert float(z.min()) == pytest.approx(-height / 2.0, abs=0.01)
    assert float(z.max()) == pytest.approx(height / 2.0, abs=0.01)


def _assert_groove_round_the_arrows(trimesh_module, stl_path, height, span, widest):
    """
    The emboss plate: on the column at both caps and outside the chain, off it
    on the first-cell side (above 180) everywhere inside, never past the widest
    swing the NOTE states.
    """
    import numpy as np

    assert _groove_cap_angles(trimesh_module, stl_path, height) == pytest.approx(
        [ARROW_DEG], abs=0.05
    )
    angles, z = _floor(trimesh_module, stl_path, height)
    assert float(z.min()) == pytest.approx(-height / 2.0, abs=0.01)
    assert float(z.max()) == pytest.approx(height / 2.0, abs=0.01)
    outside = (z < span[0] - 0.01) | (z > span[1] + 0.01)
    assert np.abs(angles[outside] - ARROW_DEG).max() < 0.05
    inside = (z > -20.0) & (z < 20.0)
    assert inside.any()
    assert angles[inside].min() > ARROW_DEG + 2.0, (
        "the groove runs on the arrows' centre line"
    )
    assert angles.max() < widest + 0.05


def _assert_arrows_whole(trimesh_module, stl_path, height, tips):
    """Every raised arrow keeps its point on the centre line, and its base corners 7.4 degrees out."""
    import numpy as np

    v, r, a = _load(trimesh_module, stl_path)
    proud = r > RADIUS + 0.05
    off = np.abs(((a - ARROW_DEG + 180.0) % 360.0) - 180.0)
    z = v[:, 2] - height / 2.0
    for tip in tips:
        assert (proud & (off < 0.5) & (np.abs(z - tip) < 0.1)).any(), (
            f"the arrow tip at z {tip} is gone"
        )
    assert (proud & (off > 6.0) & (off < 9.0) & (np.abs(z) < 21.0)).any(), (
        "the arrows' base corners are gone"
    )


def _web_path(settings, height):
    """
    The web generator's emboss-plate path for the same layout, as (physical
    degrees, z about mid-height): its spec theta is in the dot convention its
    worker negates, so the physical angle is -theta.
    """
    if not (WEB_REPO / "app" / "geometry_spec.py").exists():
        pytest.skip(f"web repository not found at {WEB_REPO} (set BRAILLE_WEB_REPO)")
    if str(WEB_REPO) not in sys.path:
        # Appended, so this repo's own `tests` package keeps winning.
        sys.path.append(str(WEB_REPO))
    from app.geometry_spec import extract_cylinder_geometry_spec
    from app.models import CardSettings
    from app.utils import braille_to_dots

    spec = extract_cylinder_geometry_spec(
        [""] * 4,
        "g1",
        CardSettings(**{"grid_rows": 4, "indicator_mode": "tactile", **settings}),
        {"diameter": 2 * RADIUS, "height": height, "seam_offset_deg": 0.0},
        None,
        "positive",
        braille_to_dots,
    )
    return [
        ((-math.degrees(point["theta"])) % 360.0, point["z"])
        for point in spec["cylinder"]["seam_channel"]["path"]
    ]


def _distance_to_polyline(point, line):
    best = math.inf
    for (x0, z0), (x1, z1) in zip(line, line[1:]):
        dx, dz = x1 - x0, z1 - z0
        t = ((point[0] - x0) * dx + (point[1] - z0) * dz) / ((dx * dx + dz * dz) or 1.0)
        t = max(0.0, min(1.0, t))
        best = min(best, math.hypot(point[0] - x0 - t * dx, point[1] - z0 - t * dz))
    return best


def _assert_floor_is_the_web_path(trimesh_module, stl_path, height, web):
    """
    In arc mm about 180 and z: every groove-floor vertex lies on the web path,
    and every web path point on the barrel has a floor vertex on it.
    """
    to_arc = math.pi * RADIUS / 180.0
    line = [((deg - ARROW_DEG) * to_arc, z) for deg, z in web]
    angles, z = _floor(trimesh_module, stl_path, height, band=0.002)
    floor = [((deg - ARROW_DEG) * to_arc, zz) for deg, zz in zip(angles, z)]
    assert floor, "no groove floor"
    worst = max(_distance_to_polyline(p, line) for p in floor)
    assert worst < 0.01, f"a floor vertex is {worst:.4f} mm off the web path"
    for point in line:
        if -height / 2.0 + 0.5 < point[1] < height / 2.0 - 0.5:
            nearest = min(math.hypot(point[0] - x, point[1] - zz) for x, zz in floor)
            assert nearest < 0.01, f"no floor vertex at the web path point {point}"


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("scad_file", [V1_FILE, V2_FILE], ids=["v1", "v2"])
def test_thirteen_cells_put_the_arrow_at_the_seam_centre_and_the_groove_round_it(
    openscad_binary, trimesh_module, tmp_path, scad_file
):
    """Arrow and recess at 180; the emboss plate's groove round the whole arrows; no card note."""
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
        span, widest = _noted_detour(output)
        assert span == pytest.approx(list(DETOUR_SPAN), abs=1e-4)
        assert widest == pytest.approx(DETOUR_MAX_DEG, abs=1e-3)
        assert "NOTE: this row needs" not in output
        assert "NOTE: The seam channel" not in output

    _assert_groove_round_the_arrows(
        trimesh_module, emboss, height, DETOUR_SPAN, DETOUR_MAX_DEG
    )
    _assert_arrows_whole(trimesh_module, emboss, height, TIPS)
    _assert_straight_groove(trimesh_module, counter, height)

    recess = _recess_angles(trimesh_module, counter, height, 9.0)
    assert len(recess) > 0
    assert (recess.min() + recess.max()) / 2.0 == pytest.approx(ARROW_DEG, abs=0.3)
    # The counter plate is unchanged: its recess still spans its full mitred
    # width (4.4 mm at the surface, 4.5 at its floor - about 17.5 degrees
    # measured on the floor vertices).
    assert 16.0 < recess.max() - recess.min() < 18.5

    assert _badge_vertices(trimesh_module, emboss, height) == 0
    assert _badge_vertices(trimesh_module, counter, height) == 0


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize(
    "scad_file, defines, web_settings",
    [
        (V1_FILE, {}, {}),
        (V2_FILE, {}, {}),
        (V1_FILE, {"integrated_gears": "On"}, {"gear_rollers_enabled": 1}),
        (
            V1_FILE,
            {"paper_thickness_preset": "0.3mm"},
            {"tactile_indicator_layout": "three_spaced"},
        ),
    ],
    ids=["v1", "v2", "v1-gears", "v1-three-arrows"],
)
def test_the_groove_floor_is_the_web_generators_path(
    openscad_binary, trimesh_module, tmp_path, scad_file, defines, web_settings
):
    """
    The two generators cut the same groove: the OpenSCAD floor and the web
    path agree to 0.01 mm, both ways - including the gear-mode weld's growth
    and the three spaced arrows.
    """
    height = HEIGHT[scad_file]
    stl_path, _ = _render(
        openscad_binary,
        tmp_path,
        scad_file,
        "parity",
        {"indicator_mode": "Tactile", "grid_columns": 13, **defines},
    )
    web = _web_path({"grid_columns": 13, **web_settings}, height)
    _assert_floor_is_the_web_path(trimesh_module, stl_path, height, web)


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_three_spaced_arrows_bring_the_groove_back_to_the_column_between_them(
    openscad_binary, trimesh_module, tmp_path
):
    """
    The 0.3mm preset's three arrows (0, +/-15 mm) are 5 mm apart, so between
    them the groove returns to 180 for 0.878 mm (z 6.061..6.939 above the
    middle arrow's tip, and the same below the top arrow's base on the other
    side of mid-height); the per-row chain never does.
    """
    import numpy as np

    height = HEIGHT[V1_FILE]
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        V1_FILE,
        "three",
        {
            "indicator_mode": "Tactile",
            "grid_columns": 13,
            "paper_thickness_preset": "0.3mm",
        },
    )
    angles, z = _floor(trimesh_module, stl_path, height)
    for low, high in ((6.0, 7.0), (-9.0, -8.0)):
        on_column = (z > low) & (z < high) & (np.abs(angles - ARROW_DEG) < 0.01)
        assert on_column.sum() >= 2, (
            f"the groove does not return to the column between z {low} and {high}"
        )
    _assert_arrows_whole(trimesh_module, stl_path, height, (20.0, 5.0, -10.0))


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
    # The arrow column does not move with the cell count: the same detour as at 13.
    span, widest = _noted_detour(output)
    assert span == pytest.approx(list(DETOUR_SPAN), abs=1e-4)
    _assert_groove_round_the_arrows(
        trimesh_module, stl_path, HEIGHT[V1_FILE], span, widest
    )
    _assert_arrows_whole(trimesh_module, stl_path, HEIGHT[V1_FILE], TIPS)


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate_type", ["Embossing Plate", "Counter Plate"])
def test_fifteen_cells_leave_the_groove_out_and_say_why(
    openscad_binary, trimesh_module, tmp_path, plate_type
):
    """
    15 cells leave 0.731 mm beside the arrow column where the detour needs 3.5:
    both plates leave the groove out and say why in S-C5, beside the seam-gap
    warning (a WARNING, hence no --hardwarnings here).
    """
    stl_path, output = _render(
        openscad_binary,
        tmp_path,
        V1_FILE,
        "fifteen",
        {"indicator_mode": "Tactile", "grid_columns": 15, "plate_type": plate_type},
        hardwarnings=False,
    )
    assert "Tactile indicator needs a seam gap of at least" in output
    assert S_C5 in output
    assert "NOTE: tactile arrow at 180 deg on both plates." in output
    assert "the seam gap is too narrow for it" not in output
    # A groove always reaches both end faces; the counter plate's bowls also
    # cross the floor radius, but never there.
    assert _groove_cap_angles(trimesh_module, stl_path, HEIGHT[V1_FILE]) == [], (
        "a groove was cut where there is no room for it"
    )
