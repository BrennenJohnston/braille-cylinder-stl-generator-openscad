"""
Render Smoke Tests for the Braille Wedge Card Generator

Renders four representative configurations through the OpenSCAD CLI and
asserts each export is a printable solid:

- watertight,
- a single connected body (dots/fins/bridges all fused -- the historical
  failure mode was dots exporting as hundreds of floating shells),
- with the bounding box the sizing math predicts.

These tests auto-skip when OpenSCAD is not installed. render_quality=Medium is
passed via -D to keep render times low; quality only affects tessellation
density, not the bounding box.

License: PolyForm Noncommercial 1.0.0
"""

import math
from pathlib import Path

import pytest
import trimesh

from conftest import SCAD_FILE
from openscad_runner import OpenSCADNotFoundError, OpenSCADRunner

# ---------------------------------------------------------------------------
# Defaults mirrored from the .scad (kept in sync by test_defaults_in_sync
# below, which parses the source).
# ---------------------------------------------------------------------------
DEFAULTS = {
    "cell_spacing": 7.0,
    "line_spacing": 10.0,
    "dot_spacing": 2.5,
    "rounded_dot_base_diameter": 1.6,
    "cone_dot_base_diameter": 1.5,
    "auto_size_margin_mm": 6.0,
    "face_angle_deg": 75.0,
    "card_thickness_mm": 1.5,
    "fin_offset_mm": 1.0,
    "fin_thickness_mm": 1.2,
    "brim_width_mm": 2.0,
}

HELLO = "⠓⠑⠇⠇⠕"  # 5 cells
WORLD = "⠺⠕⠗⠇⠙"  # 5 cells
TEN_CELLS = HELLO + WORLD

BBOX_TOL_MM = 0.3


def expected_face_size(lines, p=DEFAULTS, auto=True, manual_w=85.0, manual_h=55.0):
    """Replicates the .scad auto-size formula for the effective face (mm)."""
    if not auto:
        return manual_w, manual_h
    max_len = max(len(line) for line in lines)
    rows = max(
        (i + 1 for i, line in enumerate(lines) if len(line) > 0), default=0
    )
    max_dot_dia = max(p["rounded_dot_base_diameter"], p["cone_dot_base_diameter"])
    content_w = (max(max_len, 1) - 1) * p["cell_spacing"]
    content_h = (max(rows, 1) - 1) * p["line_spacing"]
    block_w = content_w + p["dot_spacing"] + max_dot_dia
    block_h = content_h + 2 * p["dot_spacing"] + max_dot_dia
    width = max(block_w + 2 * p["auto_size_margin_mm"], 30.0)
    height = max(block_h + 2 * p["auto_size_margin_mm"], 20.0)
    return width, height


def expected_bounds(face_w, face_h, fins_on, p=DEFAULTS):
    """Predicts the global STL bounding box for a card of the given face size."""
    angle = math.radians(p["face_angle_deg"])
    card_height = face_h * math.sin(angle)
    base_run = face_h * math.cos(angle)
    t = p["card_thickness_mm"]

    if fins_on:
        x_half = face_w / 2 + p["fin_thickness_mm"] / 2 + p["brim_width_mm"]
        y_min = -(t + p["fin_offset_mm"] + p["brim_width_mm"])
    else:
        x_half = face_w / 2
        y_min = -t

    return (
        (-x_half, y_min, 0.0),
        (x_half, base_run, card_height),
    )


@pytest.fixture(scope="module")
def runner():
    try:
        return OpenSCADRunner()
    except OpenSCADNotFoundError:
        pytest.skip("OpenSCAD not installed - skipping render smoke tests")


def render(runner, tmp_path: Path, name: str, parameters: dict) -> trimesh.Trimesh:
    output = tmp_path / f"{name}.stl"
    params = {"render_quality": "Medium", **parameters}
    result = runner.generate_stl(SCAD_FILE, output, parameters=params)
    assert result.success, (
        f"OpenSCAD render failed (rc={result.returncode}):\n{result.stderr}"
    )
    return trimesh.load(output, force="mesh")


def assert_printable(mesh: trimesh.Trimesh, bounds_expected):
    assert mesh.is_watertight, "exported STL is not watertight"
    assert mesh.body_count == 1, (
        f"exported STL has {mesh.body_count} disconnected bodies; dots, fins, "
        "bridges, and card must fuse into one printable solid"
    )
    (exp_min, exp_max) = bounds_expected
    got_min, got_max = mesh.bounds
    for axis, (e, g) in enumerate(zip(exp_min, got_min)):
        assert abs(e - g) <= BBOX_TOL_MM, (
            f"bounds min axis {axis}: expected {e:.2f}, got {g:.2f}"
        )
    for axis, (e, g) in enumerate(zip(exp_max, got_max)):
        assert abs(e - g) <= BBOX_TOL_MM, (
            f"bounds max axis {axis}: expected {e:.2f}, got {g:.2f}"
        )


def test_defaults_in_sync():
    """The DEFAULTS table above must match the .scad parameter defaults."""
    import re

    content = SCAD_FILE.read_text(encoding="utf-8")
    for name, expected in DEFAULTS.items():
        match = re.search(
            rf"^{name}\s*=\s*([\d.]+)\s*;", content, flags=re.MULTILINE
        )
        assert match, f"parameter {name} not found in .scad"
        actual = float(match.group(1))
        assert actual == pytest.approx(expected), (
            f"{name}: .scad default is {actual}, test table says {expected}. "
            "Update DEFAULTS in this file."
        )


@pytest.mark.requires_openscad
def test_default_card(runner, tmp_path):
    """First-run defaults: auto-sized two-line card with fins."""
    mesh = render(runner, tmp_path, "default", {})
    face_w, face_h = expected_face_size([HELLO, WORLD])
    assert_printable(mesh, expected_bounds(face_w, face_h, fins_on=True))


@pytest.mark.requires_openscad
def test_twenty_line_stress_card(runner, tmp_path):
    """All 20 lines filled with 10-cell text (tall card, many dots)."""
    lines = {f"Line_{n}": TEN_CELLS for n in range(1, 21)}
    mesh = render(runner, tmp_path, "twenty_line", lines)
    face_w, face_h = expected_face_size([TEN_CELLS] * 20)
    assert_printable(mesh, expected_bounds(face_w, face_h, fins_on=True))


@pytest.mark.requires_openscad
def test_fins_off_bare_card(runner, tmp_path):
    """support_fins=Off exports just the leaning card with dots."""
    mesh = render(runner, tmp_path, "fins_off", {"support_fins": "Off"})
    face_w, face_h = expected_face_size([HELLO, WORLD])
    assert_printable(mesh, expected_bounds(face_w, face_h, fins_on=False))


@pytest.mark.requires_openscad
def test_manual_size_card(runner, tmp_path):
    """Manual sizing: business-card footprint 75 x 25 mm."""
    mesh = render(
        runner,
        tmp_path,
        "manual_size",
        {
            "auto_size_card": "Off",
            "card_face_width_mm": 75,
            "card_face_height_mm": 25,
        },
    )
    face_w, face_h = expected_face_size([], auto=False, manual_w=75.0, manual_h=25.0)
    assert_printable(mesh, expected_bounds(face_w, face_h, fins_on=True))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
