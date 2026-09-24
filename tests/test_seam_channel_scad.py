"""
Slicer seam channel — the OpenSCAD side of the web app's 2026-09-20 feature.

Phase O0 of the OpenSCAD parity plan (2026-09-21) lays the baseline: the four
default plates (Version 1 and Version 2, embossing and counter) were rendered
BEFORE the channel existed and their geometry signatures recorded in
``tests/fixtures/seam_channel/hashes.json``. From phase O1 on, a render with
``seam_channel = "Off"`` must reproduce that geometry exactly - the same
"off is identical" contract the web app pins with its
``tests/e2e/fixtures/*_before_seam_channel.stl``. Today the variable does not
exist yet, so ``-D seam_channel="Off"`` is inert and the test proves only that
the baseline is what the files render right now.

Why a signature and not STLs: the counter plates are 8 MB each as binary STL
(52 MB as ASCII) and the repo tracks ``*.stl`` through Git LFS. OpenSCAD
2026.01.03 renders the same command to the same bytes (checked twice on
2026-09-21), but a CHANGED command line flips the diagonal of a few coplanar
quads on the Version 2 countersink slivers - identical vertices, different
bytes - so the contract is the geometry signature (``_signature`` below), not
the file hash, and it fits in 3 KB.

Render tests skip when no OpenSCAD binary is available. Verdicts come from the
output text and file existence, never from an exit code.

License: PolyForm Noncommercial 1.0.0
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "seam_channel"
HASHES = FIXTURES / "hashes.json"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)


@pytest.fixture(scope="module")
def openscad_binary():
    """The console wrapper, driven directly, so output text can be judged."""
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the seam channel render tests")


@pytest.fixture(scope="module")
def baseline():
    return json.loads(HASHES.read_text(encoding="utf-8"))


# The flag set every baseline render was made with. It is part of the byte
# contract: with --check-parameter-ranges=true OpenSCAD triangulates a few
# coplanar quads on the Version 2 countersink slivers with the other diagonal
# (same vertices, different bytes), so a render without it does not match.
BASELINE_FLAGS = [
    "--hardwarnings",
    "--check-parameter-ranges=true",
    "--export-format",
    "binstl",
]


def _signature(data):
    """
    The geometry of a binary STL, independent of how its quads were split.

    OpenSCAD 2026.01.03 renders identical vertices from run to run, but on a
    few coplanar quads (the Version 2 countersink slivers) it picks the other
    diagonal whenever the command line changes - same shape, different bytes.
    Triangle count, the unique vertex cloud, volume and area do not move under
    a diagonal flip, so they are what the baseline pins.
    """
    import struct

    import numpy as np

    count = struct.unpack_from("<I", data, 80)[0]
    dtype = np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")])
    tris = np.frombuffer(data, dtype=dtype, count=count, offset=84)["v"].astype(
        np.float64
    )
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    volume = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    area = float((np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2.0).sum())
    points = np.unique(np.round(tris.reshape(-1, 3), 5), axis=0)
    return {
        "tri_count": int(count),
        "unique_vertex_count": int(len(points)),
        "vertex_sha256": hashlib.sha256(points.tobytes()).hexdigest(),
        "volume_mm3": round(volume, 6),
        "area_mm2": round(area, 6),
    }


def _render(binary, scad_file, stl_path, defines, flags=BASELINE_FLAGS):
    """Render once as binary STL. Returns the combined stdout+stderr."""
    command = [str(binary), *flags]
    # One plate unless a test asks for the pair: the file's default renders both.
    defines = {"render_both_plates": "Off", **defines}
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(scad_file)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT
    )
    return (result.stdout or "") + "\n" + (result.stderr or "")


def test_baseline_records_the_four_default_plates(baseline):
    """The hash file names both files, both plates, and the binary export."""
    renders = baseline["renders"]
    assert set(renders) == {"v1_emboss", "v1_counter", "v2_emboss", "v2_counter"}
    for name, record in renders.items():
        assert (PROJECT_ROOT / record["file"]).is_file(), name
        assert record["flags"] == BASELINE_FLAGS, name
        assert record["defines"]["seam_channel"] == "Off", name
        assert len(record["vertex_sha256"]) == 64
        assert record["tri_count"] > 0 and record["unique_vertex_count"] > 0
        assert record["volume_mm3"] > 0 and record["area_mm2"] > 0
        assert record["byte_size"] == 84 + 50 * record["tri_count"]
        assert record["warnings_or_errors"] == 0


@pytest.mark.slow
@pytest.mark.parametrize("name", ["v1_emboss", "v1_counter", "v2_emboss", "v2_counter"])
def test_seam_channel_off_reproduces_the_pre_channel_bytes(
    openscad_binary, baseline, tmp_path, name
):
    """
    ``seam_channel = "Off"`` renders the exact bytes the file produced before
    the channel existed. Until phase O1 lands the define is inert, so this is
    the baseline proving itself; afterwards it is the off-state contract.
    """
    record = baseline["renders"][name]
    stl_path = tmp_path / f"{name}.stl"
    output = _render(
        openscad_binary,
        PROJECT_ROOT / record["file"],
        stl_path,
        dict(record["defines"]),
    )
    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    data = stl_path.read_bytes()
    assert len(data) == record["byte_size"], (
        f"{name}: {len(data)} bytes, baseline {record['byte_size']}"
    )
    got = _signature(data)
    want = {key: record[key] for key in got}
    assert got == want, (
        f"{name}: the Off render drifted from the baseline geometry:\n{got}\n{want}"
    )


# ---------------------------------------------------------------------------
# Phase O1: the channel in the Version 1 file
# ---------------------------------------------------------------------------

V1_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
# The web generator's copy of the constants and the two sentences. Absent on
# CI, so the cross-check skips LOUDLY rather than failing for a reason
# unrelated to this repo.
WEB_GEOMETRY_SPEC = (
    Path(
        os.environ.get(
            "BRAILLE_WEB_REPO",
            str(PROJECT_ROOT.parent / "braille-cylinder-stl-generator"),
        )
    )
    / "app"
    / "geometry_spec.py"
)
SEAM_CONSTANTS = {
    "SEAM_CHANNEL_WIDTH_MM": 1.0,
    "SEAM_CHANNEL_DEPTH_MM": 0.5,
    "SEAM_CHANNEL_MARGIN_MM": 0.25,
    "SEAM_CHANNEL_OVERSHOOT_MM": 1.0,
    "SEAM_CHANNEL_LIP_MM": 0.5,
    "SEAM_CHANNEL_MIN_WALL_MM": 1.2,
}
# S-C2 and S-C3, the web generator's own words (signed off by Brennen
# 2026-09-21), quoted here so the two generators can never drift apart.
S_C2 = "The seam channel was left out: the seam gap is too narrow for it at this cell count and diameter."
S_C3 = "The seam channel was left out: the cylinder wall would be thinner than 1.2 mm under it."
S_C3_HEAD = "The seam channel was left out: the cylinder wall would be thinner than "
# S-C5, Tactile mode's (signed off by Brennen 2026-09-23). The web module splits
# it over two string literals, so the cross-check looks for each half there.
S_C5_HEAD = "The seam channel was left out: there is not enough room for it beside the alignment arrows. "
S_C5_TAIL = "Reduce the number of braille cells, increase the cylinder diameter, or narrow the indicator."
# Worked numbers from the web spec (SURFACE_DIMENSIONS_SPECIFICATIONS.md 2.6),
# 30.8 mm, 0.4 preset: the PHYSICAL groove angles in the exported STL, as
# (embossing, counter). 15 visual columns = 13 text cells + 2 marker columns.
# Physical angles (emboss, counter). Tactile: down the arrow column itself at
# 180 on both plates since 2026-09-21 (web decisions D-T6 / D-T7), the full
# height, stepping round the raised arrows on the emboss plate since D-T8
# (2026-09-22); this file measures the end caps, where the groove is on the
# column, tests/test_tactile_seam_column_scad.py the path and the whole arrows.
GROOVE_DEG = {
    ("visual", 15): (181.67, 178.33),
    ("tactile", 14): (180.0, 180.0),
    ("tactile", 13): (180.0, 180.0),
}
RADIUS = 15.4
HEIGHT = 52.0
FLOOR_R = RADIUS - 0.5


def _scad_constant(text, name):
    found = re.search(
        rf"^\s*{re.escape(name)}\s*=\s*([0-9.+\-]+)\s*;", text, re.MULTILINE
    )
    assert found, f"{name} not found"
    return float(found.group(1))


def test_v1_declares_the_switch_on_by_default():
    text = V1_FILE.read_text(encoding="utf-8")
    assert re.search(r'^seam_channel = "On"; // \[On, Off\]$', text, re.MULTILINE)
    assert 'seam_channel_on = (seam_channel == "On") || (seam_channel == "on");' in text
    # The comment directly above the parameter is what the Customizer shows as
    # its description: it carries the sentence and no development tag.
    description = text.split('seam_channel = "On";')[0].splitlines()[-1]
    assert description.startswith("// A shallow groove"), description
    assert "DRAFT" not in description and "Brennen" not in description


def test_v1_constants_and_sentences_mirror_the_web_generator():
    text = V1_FILE.read_text(encoding="utf-8")
    here = {name: _scad_constant(text, name) for name in SEAM_CONSTANTS}
    assert here == SEAM_CONSTANTS
    assert f'echo("NOTE: {S_C2}");' in text
    assert f'"NOTE: {S_C3_HEAD}"' in text
    assert f'echo("NOTE: {S_C5_HEAD}{S_C5_TAIL}");' in text
    if not WEB_GEOMETRY_SPEC.exists():
        pytest.skip(
            f"web repository not found at {WEB_GEOMETRY_SPEC.parents[1]} (set BRAILLE_WEB_REPO)"
        )
    web = WEB_GEOMETRY_SPEC.read_text(encoding="utf-8")
    for name, value in here.items():
        there = re.search(rf"^{name} = ([0-9.]+)", web, re.MULTILINE)
        assert there, f"the web generator no longer declares {name}"
        assert float(there.group(1)) == value, f"{name} drifted between the generators"
    assert S_C2 in web
    assert S_C3_HEAD in web
    assert S_C5_HEAD in web and S_C5_TAIL in web


def _groove_cap_angles(trimesh_module, stl_path):
    """Angles (deg, 0..360) of the end-cap vertices on the groove floor radius."""
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    caps = (np.abs(v[:, 2]) < 0.01) | (np.abs(v[:, 2] - HEIGHT) < 0.01)
    floor = caps & (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03)
    return sorted(
        set(np.round(np.degrees(np.arctan2(v[floor, 1], v[floor, 0])) % 360.0, 2))
    )


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.mark.slow
@pytest.mark.parametrize(
    ("mode", "columns", "plate", "which"),
    [
        ("visual", 15, "Embossing Plate", 0),
        ("visual", 15, "Counter Plate", 1),
        ("tactile", 14, "Embossing Plate", 0),
        ("tactile", 14, "Counter Plate", 1),
        ("tactile", 13, "Embossing Plate", 0),
        ("tactile", 13, "Counter Plate", 1),
    ],
)
def test_v1_groove_sits_at_the_web_angle(
    openscad_binary, trimesh_module, tmp_path, mode, columns, plate, which
):
    """One groove per plate, at the physical angle the web STL carries, mirrored between the plates."""
    defines = {
        "plate_type": plate,
        "indicator_mode": "Tactile" if mode == "tactile" else "Visual",
    }
    if mode == "tactile":
        defines["grid_columns"] = columns
        if columns == 14:
            # 14 cells run off a 90 mm card and grow the red badge (its
            # letters are loose bodies). The groove is what is under test,
            # so declare a longer card - the geometry below is unchanged.
            defines["CARD_LENGTH_MM"] = 100
    stl_path = tmp_path / "plate.stl"
    output = _render(openscad_binary, V1_FILE, stl_path, defines)
    assert "ERROR:" not in output and "WARNING:" not in output, output[:800]
    assert "NOTE: The seam channel" not in output
    angles = _groove_cap_angles(trimesh_module, stl_path)
    expected = GROOVE_DEG[(mode, columns)][which]
    assert angles, "no groove floor on the end caps"
    assert all(abs(a - expected) < 0.05 for a in angles), (
        f"groove at {angles}, expected {expected}"
    )
    mesh = trimesh_module.load(str(stl_path), force="mesh")
    assert len(mesh.split(only_watertight=False)) == 1


@pytest.mark.slow
def test_v1_groove_is_left_out_when_the_visual_gap_is_too_narrow(
    openscad_binary, trimesh_module, tmp_path
):
    """16 visual columns (14 cells + 2 markers): no window (the web omits it too) - NOTE, badge, no floor."""
    stl_path = tmp_path / "plate.stl"
    output = _render(
        openscad_binary,
        V1_FILE,
        stl_path,
        {
            "plate_type": "Embossing Plate",
            "indicator_mode": "Visual",
            "grid_columns": 14,
        },
    )
    assert f"NOTE: {S_C2}" in output
    assert _groove_cap_angles(trimesh_module, stl_path) == []
    # The badge renders as text bodies beside the plate, so the body count grows.
    assert (
        len(
            trimesh_module.load(str(stl_path), force="mesh").split(
                only_watertight=False
            )
        )
        > 1
    )


@pytest.mark.slow
def test_v1_tactile_15_columns_leave_the_groove_out_and_say_why(
    openscad_binary, trimesh_module, tmp_path
):
    """
    Since D-T8 the emboss plate's groove steps round the arrows on the
    first-cell side, which needs 3.5 mm there; 15 cells leave 0.731 mm, so
    the groove is left out with S-C5 beside the seam-GAP warning.
    """
    stl_path = tmp_path / "plate.stl"
    output = _render(
        openscad_binary,
        V1_FILE,
        stl_path,
        {
            "plate_type": "Embossing Plate",
            "indicator_mode": "Tactile",
            "grid_columns": 15,
        },
    )
    assert "Tactile indicator needs a seam gap of at least" in output
    assert f"NOTE: {S_C5_HEAD}{S_C5_TAIL}" in output
    assert _groove_cap_angles(trimesh_module, stl_path) == []


@pytest.mark.slow
def test_v1_groove_is_left_out_when_the_wall_would_be_too_thin(
    openscad_binary, trimesh_module, tmp_path
):
    """A 13.5 mm cutout (circumradius 13.977) leaves 0.923 mm under the apex: omitted with S-C3.

    The cutout radius is preset-owned, so the preset is set to Custom first; a
    -D on the radius alone is silently ignored (research memory, 2026-08).
    """
    stl_path = tmp_path / "plate.stl"
    output = _render(
        openscad_binary,
        V1_FILE,
        stl_path,
        {
            "plate_type": "Embossing Plate",
            "paper_thickness_preset": "Custom",
            "polygon_cutout_radius_mm": 13.5,
        },
    )
    assert "ERROR:" not in output and "WARNING:" not in output, output[:800]
    assert f"NOTE: {S_C3}" in output
    assert _groove_cap_angles(trimesh_module, stl_path) == []


@pytest.mark.slow
def test_v1_groove_survives_gear_mode(openscad_binary, trimesh_module, tmp_path):
    """Gears on: the groove is cut before the gears join, and the roller is still one body."""
    stl_path = tmp_path / "plate.stl"
    output = _render(
        openscad_binary,
        V1_FILE,
        stl_path,
        {"plate_type": "Embossing Plate", "integrated_gears": "On"},
    )
    assert "ERROR:" not in output and "WARNING:" not in output, output[:800]
    assert "NOTE: The seam channel" not in output
    mesh = trimesh_module.load(str(stl_path), force="mesh")
    assert len(mesh.split(only_watertight=False)) == 1
    v = mesh.vertices
    assert abs(v[:, 2].min() + 10.0) < 0.01 and abs(v[:, 2].max() - 62.0) < 0.01
    # The gear faces meet the groove at the barrel ends: floor vertices at z 0 and 52.
    angles = _groove_cap_angles(trimesh_module, stl_path)
    assert angles and all(abs(a - 181.67) < 0.05 for a in angles), angles


# ---------------------------------------------------------------------------
# Phase O2: the channel in the Version 2 file (54 mm barrel, keyed bore)
# ---------------------------------------------------------------------------

V2_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"
V2_HEIGHT = 54.0


def test_v2_declares_the_same_switch_constants_and_sentences():
    """The self-contained Version 2 file carries the identical port."""
    text = V2_FILE.read_text(encoding="utf-8")
    assert re.search(r'^seam_channel = "On"; // \[On, Off\]$', text, re.MULTILINE)
    assert {
        name: _scad_constant(text, name) for name in SEAM_CONSTANTS
    } == SEAM_CONSTANTS
    assert f'echo("NOTE: {S_C2}");' in text
    assert f'"NOTE: {S_C3_HEAD}"' in text
    description = text.split('seam_channel = "On";')[0].splitlines()[-1]
    assert description.startswith("// A shallow groove"), description
    assert "DRAFT" not in description and "Brennen" not in description
    # Cut first in the Version 2 shell, before the keyed halves.
    shell = text.split("module cylinder_shell_v2(")[1].split("keyed_half_cutout(")[0]
    assert "seam_channel_cut(channel_theta_deg)" in shell


def _groove_cap_angles_at(trimesh_module, stl_path, height):
    import numpy as np

    v = trimesh_module.load(str(stl_path), force="mesh").vertices
    r = np.hypot(v[:, 0], v[:, 1])
    caps = (np.abs(v[:, 2]) < 0.01) | (np.abs(v[:, 2] - height) < 0.01)
    floor = caps & (r > FLOOR_R - 0.03) & (r < FLOOR_R + 0.03)
    return sorted(
        set(np.round(np.degrees(np.arctan2(v[floor, 1], v[floor, 0])) % 360.0, 2))
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    ("plate", "expected"),
    [("Embossing Plate", 181.67), ("Counter Plate", 178.33)],
)
def test_v2_groove_sits_at_the_web_angle(
    openscad_binary, trimesh_module, tmp_path, plate, expected
):
    """Same physical angles on the 54 mm barrel; the keyed bore never reaches the floor."""
    stl_path = tmp_path / "plate.stl"
    output = _render(openscad_binary, V2_FILE, stl_path, {"plate_type": plate})
    assert "ERROR:" not in output and "WARNING:" not in output, output[:800]
    assert "NOTE: The seam channel" not in output
    angles = _groove_cap_angles_at(trimesh_module, stl_path, V2_HEIGHT)
    assert angles and all(abs(a - expected) < 0.05 for a in angles), (
        f"groove at {angles}, expected {expected}"
    )
    mesh = trimesh_module.load(str(stl_path), force="mesh")
    assert len(mesh.split(only_watertight=False)) == 1
