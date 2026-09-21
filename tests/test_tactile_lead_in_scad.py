"""
The tactile arrow lead-in (2026-09-21, web decisions D-T1..D-T4) - renders of
both files.

What this proves about the files the user actually renders:

  * the emboss plate's raised arrow and the counter plate's recess sit at the
    angles the render's NOTE announces - 195.0 / 165.0 degrees at 13 cells on
    the 30.8 mm barrel - a fixed 5.35 mm lead-in before the first cell, and
    the two plates reflect about 180 so the pair still meets at the nip;
  * the seam channel now runs BEHIND the arrow (169.95 / 190.05 degrees);
  * 14 cells render, with the card-fit NOTE and the red badge above the
    cylinder; 13 cells render with neither;
  * the Version 2 file places its arrow identically.

Judged by OUTPUT TEXT and FILE EXISTENCE, never by an exit code (the rule the
other render suites follow). Render tests skip without OpenSCAD.

License: PolyForm Noncommercial 1.0.0
"""

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
LEAD_IN_MM = 5.35  # 2.0 + 0.2 + 1.0 + (1.25 + 0.9) at the 0.4mm preset
ARROW_DEG = {13: 194.996, 14: 182.904}  # emboss; the counter plate is 360 minus these
GROOVE_DEG = (169.95, 190.05)  # emboss, counter
CARD_NOTE = "NOTE: this row needs 92 mm of card from the alignment arrow; the card is 90 mm. Lower grid_columns to 13 or fewer."


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
    pytest.skip("OpenSCAD not available for the tactile lead-in render tests")


def _render(binary, tmp_path, scad_file, name, defines):
    stl_path = tmp_path / f"{name}.stl"
    command = [str(binary), "--hardwarnings", "--check-parameter-ranges=true"]
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
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    return stl_path, output


def _noted_angles(output):
    match = re.search(
        r"tactile arrow lead-in ([0-9.]+) mm; arrow at ([0-9.]+) deg on the emboss plate, "
        r"([0-9.]+) deg on the counter plate",
        output,
    )
    assert match, f"no tactile arrow NOTE:\n{output[:800]}"
    return float(match.group(1)), float(match.group(2)), float(match.group(3))


def _feature_angles(
    trimesh_module, stl_path, height, centre_deg, raised, half_window_deg
):
    """Angles of the arrow's own vertices: proud of the shell (raised) or below it (recess)."""
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    a = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
    near = np.abs(((a - centre_deg + 180.0) % 360.0) - 180.0) < half_window_deg
    inside = (v[:, 2] > 1.0) & (v[:, 2] < height - 1.0)
    radial = (
        (r > RADIUS + 0.05) if raised else ((r < RADIUS - 0.05) & (r > RADIUS - 1.0))
    )
    return a[near & inside & radial]


def _groove_cap_angles(trimesh_module, stl_path, height):
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    caps = (np.abs(v[:, 2]) < 0.01) | (np.abs(v[:, 2] - height) < 0.01)
    floor = caps & (r > RADIUS - 0.53) & (r < RADIUS - 0.47)
    return sorted(
        set(np.round(np.degrees(np.arctan2(v[floor, 1], v[floor, 0])) % 360.0, 2))
    )


def _badge_vertices(trimesh_module, stl_path, height):
    """Vertices well above the top face: the red badge text (the Version 2 nub stops at +3 mm)."""
    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    return int((v[:, 2] > height + 4.0).sum())


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("scad_file", [V1_FILE, V2_FILE], ids=["v1", "v2"])
def test_thirteen_cells_put_the_arrow_a_lead_in_before_column_0(
    openscad_binary, trimesh_module, tmp_path, scad_file
):
    """Emboss arrow at 195.0 deg, its recess at 165.0, groove behind them, no card note."""
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
        lead_in, theta_e, theta_c = _noted_angles(output)
        assert lead_in == pytest.approx(LEAD_IN_MM, abs=1e-6)
        assert theta_e == pytest.approx(ARROW_DEG[13], abs=0.01)
        assert theta_e + theta_c == pytest.approx(360.0, abs=1e-6)
        assert "NOTE: this row needs" not in output

    raised = _feature_angles(trimesh_module, emboss, height, ARROW_DEG[13], True, 12.0)
    assert len(raised) > 0
    assert float(np.median(raised)) == pytest.approx(ARROW_DEG[13], abs=0.3)
    # The 4 mm arrow spans +/- 7.44 deg at this radius.
    assert raised.min() == pytest.approx(ARROW_DEG[13] - 7.44, abs=0.3)
    assert raised.max() == pytest.approx(ARROW_DEG[13] + 7.44, abs=0.3)

    recess = _feature_angles(
        trimesh_module, counter, height, 360.0 - ARROW_DEG[13], False, 9.0
    )
    assert len(recess) > 0
    assert (recess.min() + recess.max()) / 2.0 == pytest.approx(
        360.0 - ARROW_DEG[13], abs=0.3
    )

    assert _groove_cap_angles(trimesh_module, emboss, height) == pytest.approx(
        [GROOVE_DEG[0]], abs=0.05
    )
    assert _groove_cap_angles(trimesh_module, counter, height) == pytest.approx(
        [GROOVE_DEG[1]], abs=0.05
    )
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
    lead_in, theta_e, _ = _noted_angles(output)
    assert theta_e == pytest.approx(ARROW_DEG[14], abs=0.01)
    assert CARD_NOTE in output
    assert _badge_vertices(trimesh_module, stl_path, HEIGHT[V1_FILE]) > 0
    # The groove keeps its fixed distance behind the arrow: the same angle as at 13.
    assert _groove_cap_angles(
        trimesh_module, stl_path, HEIGHT[V1_FILE]
    ) == pytest.approx([GROOVE_DEG[0]], abs=0.05)


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_a_gap_too_small_for_the_lead_in_keeps_the_arrow_centred(
    openscad_binary, tmp_path
):
    """15 cells: the arc clamps to 0, the arrow stays at 180 and the gap warning speaks."""
    stl_path = tmp_path / "emboss15.stl"
    command = [
        str(openscad_binary),
        "--check-parameter-ranges=true",
        "-D",
        'indicator_mode="Tactile"',
        "-D",
        "grid_columns=15",
        "-o",
        str(stl_path),
        str(V1_FILE),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=600, cwd=PROJECT_ROOT
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    _, theta_e, theta_c = _noted_angles(output)
    assert theta_e == 180.0 and theta_c == 180.0
    assert "Tactile indicator needs a seam gap of at least" in output
