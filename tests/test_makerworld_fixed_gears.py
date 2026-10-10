"""
The MakerWorld fixed-gear upload (2026-10-07).

MakerWorld's Parametric Model Maker takes one .scad file and no mesh files, so
the standard Version 2 upload hides its gear switch: with the switch on, the
gear meshes cannot load and only the hidden weld rings, notch fills and vent
are left. makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2_Fixed_Gears.scad
carries the meshes inside the file instead. scripts/build_makerworld_fixed_gears.py
writes it from the standard Version 2 upload and assets/v2_gears_{a,b}.stl;
these guards keep it current and faithful:

* the file is exactly what the script writes today, so a change to the
  standard upload or a regenerated gear asset cannot leave it stale;
* the inlined meshes ARE the assets, every triangle and every float32
  coordinate;
* the gears are on and out of the Customizer, and no import() is left;
* with OpenSCAD, a render is the desktop build's fused roller.

License: PolyForm Noncommercial 1.0.0
"""

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

import build_makerworld_fixed_gears as builder  # noqa: E402
from test_seam_channel_scad import _render, _signature  # noqa: E402
from test_text_too_long import _resolve_openscad_path  # noqa: E402

FIXED = builder.TARGET
V2_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"
FIRST_HIDDEN = "/* [Hidden] */"


@pytest.fixture(scope="module")
def text():
    assert FIXED.exists(), f"{FIXED.name} is missing: run scripts/build_makerworld_fixed_gears.py"
    return FIXED.read_text(encoding="utf-8")


def test_the_file_is_what_the_script_writes(text):
    assert text == builder.build(), (
        f"{FIXED.name} is out of date: run python scripts/build_makerworld_fixed_gears.py"
    )


def _inlined_mesh(text, name):
    """Parse one generated mesh function back into points and faces."""
    start = text.index(f"function {name}() = [[")
    end = text.index("]];", start)
    body = text[start + len(f"function {name}() = [[") : end]
    point_text, face_text = body.split("], [", 1)
    points = [
        tuple(float(c) for c in group.split(","))
        for group in re.findall(r"\[([^\[\]]+)\]", point_text)
    ]
    faces = [tuple(int(i) for i in group.split(",")) for group in re.findall(r"\[([^\[\]]+)\]", face_text)]
    return points, faces


@pytest.mark.parametrize("name,path", builder.MESHES, ids=[n for n, _ in builder.MESHES])
def test_the_inlined_mesh_is_the_asset(text, name, path):
    """Same triangles, same float32 coordinates, winding turned for polyhedron()."""
    points, faces = _inlined_mesh(text, name)
    rebuilt = [(points[a], points[c], points[b]) for a, b, c in faces]
    assert rebuilt == builder.read_stl(path), f"{name} no longer matches {path.name}"
    assert len(set(points)) == len(points), f"{name} repeats a point"


def test_the_gears_are_on_and_out_of_the_customizer(text):
    visible = text[: text.index(FIRST_HIDDEN)]
    assert not re.search(r"^integrated_gears\s*=", visible, re.MULTILINE), "the switch is a dial"
    declarations = re.findall(r'^integrated_gears\s*=\s*"(\w+)";', text, re.MULTILINE)
    assert declarations == ["On"], declarations
    assert "/* [Gears] */" not in text


def test_the_size_and_the_clearances_are_hidden(text):
    """The gears fit only 30.8 x 54 mm, and a fused roller has no keyed holes."""
    visible = text[: text.index(FIRST_HIDDEN)]
    for name in ("cylinder_diameter_mm", "cylinder_height_mm") + tuple(
        f"key_clearance_{gear}_mm" for gear in ("a1", "a2", "b1", "b2")
    ):
        assert not re.search(rf"^{name}\s*=", visible, re.MULTILINE), f"{name} is still a dial"
        assert re.search(rf"^{name}\s*=", text, re.MULTILINE), f"{name} is gone; the geometry reads it"


def test_no_import_is_left(text):
    code = "\n".join(line.split("//", 1)[0] for line in text.splitlines())
    assert "import(" not in code
    assert code.count("polyhedron(") == 1


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
    pytest.skip("OpenSCAD not available for the fixed-gear render test")


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_a_render_is_the_desktop_fused_roller(openscad_binary, tmp_path, plate):
    """
    The same plate from this file and from the desktop file with its gears on:
    triangle count, vertex cloud, volume and area match, so MakerWorld builds
    the roller the desktop build does.
    """
    fixed_stl, desktop_stl = tmp_path / "fixed.stl", tmp_path / "desktop.stl"
    out_fixed = _render(openscad_binary, FIXED, fixed_stl, {"plate_type": plate})
    out_desktop = _render(
        openscad_binary, V2_FILE, desktop_stl, {"plate_type": plate, "integrated_gears": "On"}
    )
    for output in (out_fixed, out_desktop):
        assert "WARNING:" not in output and "ERROR:" not in output, output[:800]
    assert _signature(fixed_stl.read_bytes()) == _signature(desktop_stl.read_bytes())
