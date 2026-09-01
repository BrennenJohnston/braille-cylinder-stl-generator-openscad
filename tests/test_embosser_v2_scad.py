"""
Embosser Version 2 (keyed gear pegs) — renders of Braille_Cylinder_STL_Generator_EmbosserV2.scad.

What this proves about the file the user actually renders:

  * both plates render clean and export ONE body;
  * the keyed cutout is a THROUGH-hole, not two blind pockets;
  * each of the four pockets is the right R14 key, grown by the clearance
    actually rendered, with a flat facing the tactile arrow column;
  * all four mouths carry the same 45 degree countersink;
  * each plate stands its key nub on the arrow column, 3 mm proud - A the
    triangle, B the square - over a matching socket in its bottom face;
  * the clearance dial reaches the geometry and its range assert bites;
  * the size note speaks as NOTE:, never WARNING:;
  * the Version 1 files were not touched;
  * every Version 2 number in the .scad still equals the web generator's.

Judged by OUTPUT TEXT and FILE EXISTENCE, never by an exit code — the same
rule test_gear_rollers_scad.py follows, and for the same reason: these tests
need to assert on a render that is SUPPOSED to fail.

Render tests skip when no OpenSCAD binary is available; the source guards run
everywhere, including the no-OpenSCAD CI job.

License: PolyForm Noncommercial 1.0.0
"""

import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"
# The Version 1 SOURCE files. Deliberately the three .scad files and not the
# whole makerworld/ directory: that folder's README documents every build in
# the repo, Version 2 included, so guarding the directory would fail the moment
# Version 2 was written up. What must never change is the v1 geometry.
V1_FILES = (
    "Braille_Cylinder_STL_Generator.scad",
    "presets.scad",
    "makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad",
)

# Family R14, inlined rather than read from the research folder: the CI machine
# has no such folder, and a test that quietly skips proves nothing.
KEY_CORNER_R = 0.5
KEYS = {  # plate -> (bottom key, top key), each [length (on 90/270), width (on 0/180)]
    "Embossing Plate": ((18.0, 10.0), (14.0, 14.0)),
    "Counter Plate": ((20.0, 8.0), (16.0, 12.0)),
}
DEFAULT_CLEARANCE = 0.110
COUNTERSINK_OFFSET = 2.0
COUNTERSINK_DEPTH = 2.0

BARREL_D = 30.8
# 54 since 2026-08-31: 1 mm of card shelf past each edge of the 52 mm card,
# Version 2's alone - the project/Version 1 default returned to 52 the same day.
BARREL_H = 54.0
NUB_HEIGHT = 3.0
NUB_AREA_AT_ZERO = 11.144  # mm^2, the profile area before the clearance inset
ARROW_COLUMN_DEG = 180.0

# The anti-rotation features, new on 2026-08-29 (D-R3-2..D-R3-5). Both plates
# now stand a nub above the top face and sink a socket into the bottom one, and
# the two plates' shapes differ: a triangle on Cylinder A, a square on B.
# Section areas in mm^2, matching app/geometry/version2.py in the web repo.
ANTIROT_CLEARANCE = 0.15
SOCKET_DEPTH = NUB_HEIGHT + ANTIROT_CLEARANCE
ANTIROT_NUB_AREA = {"Embossing Plate": 7.0461, "Counter Plate": 9.0000}
ANTIROT_SOCKET_AREA = {"Embossing Plate": 11.0980, "Counter Plate": 10.8707}

# Sections taken in the straight part of each half, clear of both countersinks.
BOTTOM_PROBE_Z = 8.0
TOP_PROBE_Z = 45.0

SIZE_NOTE_START = "NOTE: The Version 2 embosser expects a 30.8 mm x 54 mm cylinder."
PROTOTYPE_NOTE_START = "NOTE: Embosser Version 2 is a work-in-progress prototype."

# The web generator's copy of the same numbers. Absent on CI, so the
# cross-check skips rather than failing for a reason unrelated to this repo.
WEB_VERSION2 = (
    PROJECT_ROOT.parent
    / "braille-cylinder-stl-generator"
    / "app"
    / "geometry"
    / "version2.py"
)


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.fixture(scope="module")
def openscad_binary():
    """The console wrapper, driven directly: these tests assert on a FAILED render."""
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the Version 2 render tests")


@pytest.fixture(scope="module")
def source_text():
    return V2_FILE.read_text(encoding="utf-8")


def _render(binary, tmp_path, name, defines):
    """Render once. Returns (stl_path, combined output, returncode)."""
    stl_path = tmp_path / f"{name}.stl"
    command = [str(binary), "--hardwarnings", "--check-parameter-ranges=true"]
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(V2_FILE)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=600, cwd=PROJECT_ROOT
    )
    return (
        stl_path,
        (result.stdout or "") + "\n" + (result.stderr or ""),
        result.returncode,
    )


def _load(trimesh_module, stl_path, output):
    """Judge by output text and file existence, never by an exit code."""
    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    mesh = trimesh_module.load(str(stl_path), file_type="stl", force="mesh")
    mesh.merge_vertices()
    return mesh


def _strip_comments(text):
    """Source with // and /* */ comments removed, for the structural pins."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", text)


def _hole_loop(mesh, z):
    """The inner loop of the horizontal section at `z`, centred on the axis."""
    import numpy as np

    section = mesh.section(plane_origin=[0.0, 0.0, z], plane_normal=[0.0, 0.0, 1.0])
    assert section is not None, f"the plane z={z} misses the mesh"
    loops = [np.asarray(loop)[:, :2] for loop in section.discrete]
    # The barrel rim is the loop that reaches furthest out; the hole is the
    # remaining loop that encloses the axis.
    inner = [
        loop
        for loop in loops
        if np.hypot(loop[:, 0], loop[:, 1]).max() < BARREL_D / 2 - 1.0
    ]
    assert inner, f"no hole loop at z={z}"
    # Since 2026-08-29 a section near the bottom face meets TWO inner loops -
    # the keyed hole and the anti-rotation socket. The keyed hole is the one
    # centred on the axis; the socket sits out at r ~ 11.5 on the arrow column.
    return min(inner, key=lambda loop: math.hypot(loop[:, 0].mean(), loop[:, 1].mean()))


def _polygon_area(points):
    x, y = points[:, 0], points[:, 1]
    return abs(
        0.5
        * float(
            sum(
                x[i] * y[(i + 1) % len(x)] - x[(i + 1) % len(x)] * y[i]
                for i in range(len(x))
            )
        )
    )


def _polygon_centroid(points):
    """
    The area-weighted centroid, NOT the mean of the vertices.

    A mesh section puts vertices wherever facets happen to cross the plane, so
    the vertex mean is pulled toward whichever edge got tessellated finest - it
    read 180.30 degrees for the triangle and 181.51 for the square where both
    are exactly on the column.
    """
    import numpy as np

    x, y = points[:, 0], points[:, 1]
    next_x, next_y = np.roll(x, -1), np.roll(y, -1)
    cross = x * next_y - next_x * y
    area = cross.sum() / 2.0
    assert abs(area) > 1e-9, "a degenerate loop has no centroid"
    return (
        float(((x + next_x) * cross).sum() / (6.0 * area)),
        float(((y + next_y) * cross).sum() / (6.0 * area)),
    )


def _rounded_rect_area(length, width, clearance):
    r = KEY_CORNER_R + clearance
    return (length + 2 * clearance) * (width + 2 * clearance) - (4 - math.pi) * r * r


# ---------------------------------------------------------------------------
# The rendered solid
# ---------------------------------------------------------------------------


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_version2_plate_renders_as_one_body(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    Both plates render clean and export exactly ONE body.

    The emboss plate manages one body here - unlike the web export - because
    DOT_BASE_EMBED sinks each dot's base below the shell facet, which is the
    fix this repo already carries for the dome tangency.
    """
    name = "v2_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"plate_type": plate}
    )
    mesh = _load(trimesh_module, stl_path, output)

    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 1, f"{plate} exported {len(bodies)} bodies"
    assert mesh.is_watertight
    assert mesh.volume > 0, "a negative volume would mean an enclosed void"

    # Both plates carry a nub since 2026-08-29, so both reach the same height.
    expected_top = BARREL_H + NUB_HEIGHT
    assert mesh.bounds[0][2] == pytest.approx(0.0, abs=1e-3)
    assert mesh.bounds[1][2] == pytest.approx(expected_top, abs=1e-3)


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_the_keyed_cutout_goes_all_the_way_through(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """A through-hole, not two blind pockets: the axis is air from end to end."""
    import numpy as np

    name = "v2_through_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"plate_type": plate}
    )
    mesh = _load(trimesh_module, stl_path, output)

    axis = np.array([[0.0, 0.0, float(z)] for z in range(1, int(BARREL_H))])
    assert not mesh.contains(axis).any(), (
        "the axis is not clear - the hole is blind somewhere"
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_each_pocket_is_its_own_r14_key(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    Each half carries the key it should, at the size the clearance makes it,
    with a FLAT facing the tactile arrow column.

    The long dimension lies on 90/270 degrees and the short on 0/180, which is
    what puts a flat on the arrow column at 180.
    """
    import numpy as np

    name = "v2_pockets_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"plate_type": plate}
    )
    mesh = _load(trimesh_module, stl_path, output)

    bottom_key, top_key = KEYS[plate]
    for z, (length, width) in ((BOTTOM_PROBE_Z, bottom_key), (TOP_PROBE_Z, top_key)):
        loop = _hole_loop(mesh, z)
        half_w = (width + 2 * DEFAULT_CLEARANCE) / 2
        half_l = (length + 2 * DEFAULT_CLEARANCE) / 2

        assert np.abs(loop[:, 0]).max() == pytest.approx(half_w, abs=0.02), (
            f"x extent at z={z}"
        )
        assert np.abs(loop[:, 1]).max() == pytest.approx(half_l, abs=0.02), (
            f"y extent at z={z}"
        )
        assert _polygon_area(loop) == pytest.approx(
            _rounded_rect_area(length, width, DEFAULT_CLEARANCE), abs=0.5
        ), f"section area at z={z}"

        # The flat on the arrow column. Interpolated along the edge that
        # crosses y = 0, NOT sampled from vertices: a straight flat carries no
        # vertex in its middle - that is exactly what makes it flat - so
        # looking for a vertex near y = 0 finds nothing even when the flat is
        # there.
        crossings = []
        for index in range(len(loop)):
            x0, y0 = loop[index]
            x1, y1 = loop[(index + 1) % len(loop)]
            if y0 == y1 or (y0 > 0) == (y1 > 0):
                continue
            crossings.append(x0 + (-y0 / (y1 - y0)) * (x1 - x0))
        assert crossings, f"the outline never crosses the arrow column at z={z}"
        assert min(crossings) == pytest.approx(-half_w, abs=0.02), (
            f"the arrow column at z={z} does not face a flat"
        )


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_all_four_mouths_carry_the_same_45_degree_countersink(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    One rule at every mouth: the profile grown by 2.0 mm at the face, tapering
    to the hole profile 2.0 mm in. At depth d the growth is (2.0 - d), which is
    what makes it 45 degrees.
    """
    import numpy as np

    name = "v2_mouths_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"plate_type": plate}
    )
    mesh = _load(trimesh_module, stl_path, output)

    bottom_key, top_key = KEYS[plate]
    for face_z, sign, (length, width) in (
        (0.0, +1, bottom_key),
        (BARREL_H, -1, top_key),
    ):
        for depth in (0.1, 1.0, 1.9):
            grown = DEFAULT_CLEARANCE + (COUNTERSINK_OFFSET - depth)
            loop = _hole_loop(mesh, face_z + sign * depth)
            assert np.abs(loop[:, 0]).max() == pytest.approx(
                (width + 2 * grown) / 2, abs=0.02
            ), f"mouth width at z={face_z + sign * depth}"
            assert np.abs(loop[:, 1]).max() == pytest.approx(
                (length + 2 * grown) / 2, abs=0.02
            ), f"mouth length at z={face_z + sign * depth}"


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_each_plate_stands_its_own_nub_on_the_arrow_column(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    Both plates stand a 3 mm nub proud of the top face, centred on the arrow
    column - a triangle on Cylinder A, a square on B.

    The "Cylinder B has no nub" rule retired on 2026-08-29, when every gear
    gained an anti-rotation feature. Reach along the column is measured rather
    than the widest POINT, because a square's widest point is a corner sitting
    6.6 degrees off the column and the apex test the triangle allowed does not
    generalise.
    """
    import numpy as np

    name = "v2_nub_" + plate.split()[0].lower()
    stl, out, _ = _render(openscad_binary, tmp_path, name, {"plate_type": plate})
    mesh = _load(trimesh_module, stl, out)

    above = mesh.vertices[mesh.vertices[:, 2] > BARREL_H + 1e-3]
    assert len(above) > 0, f"no nub on the {plate}"
    assert mesh.bounds[1][2] == pytest.approx(BARREL_H + NUB_HEIGHT, abs=1e-3)

    section = mesh.section(
        plane_origin=[0.0, 0.0, BARREL_H + NUB_HEIGHT / 2.0],
        plane_normal=[0.0, 0.0, 1.0],
    )
    assert section is not None
    loops = [np.asarray(loop)[:, :2] for loop in section.discrete]
    assert len(loops) == 1, "only the nub stands above the top face"
    assert _polygon_area(loops[0]) == pytest.approx(ANTIROT_NUB_AREA[plate], abs=0.1)
    assert _polygon_area(loops[0]) < NUB_AREA_AT_ZERO

    # Centred on the column, and symmetric about it.
    centre = _polygon_centroid(loops[0])
    angle = math.degrees(math.atan2(centre[1], centre[0])) % 360.0
    assert angle == pytest.approx(ARROW_COLUMN_DEG, abs=0.05)
    assert loops[0][:, 1].max() == pytest.approx(-loops[0][:, 1].min(), abs=0.01)


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", list(KEYS))
def test_each_plate_sinks_its_own_socket_into_the_bottom_face(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    The matching socket: a BLIND pocket of SOCKET_DEPTH in the bottom face, on
    the arrow column, separate from the keyed hole rather than a lobe of it.
    """
    import numpy as np

    name = "v2_socket_" + plate.split()[0].lower()
    stl, out, _ = _render(openscad_binary, tmp_path, name, {"plate_type": plate})
    mesh = _load(trimesh_module, stl, out)

    section = mesh.section(
        plane_origin=[0.0, 0.0, SOCKET_DEPTH / 2.0], plane_normal=[0.0, 0.0, 1.0]
    )
    assert section is not None
    loops = [np.asarray(loop)[:, :2] for loop in section.discrete]
    inner = [
        loop
        for loop in loops
        if np.hypot(loop[:, 0], loop[:, 1]).max() < BARREL_D / 2 - 1.0
    ]
    assert len(inner) == 2, (
        f"expected the keyed hole AND the socket at mid-depth, found {len(inner)}"
    )

    socket = max(
        inner, key=lambda loop: math.hypot(loop[:, 0].mean(), loop[:, 1].mean())
    )
    assert _polygon_area(socket) == pytest.approx(ANTIROT_SOCKET_AREA[plate], abs=0.1)

    centre = _polygon_centroid(socket)
    angle = math.degrees(math.atan2(centre[1], centre[0])) % 360.0
    assert angle == pytest.approx(ARROW_COLUMN_DEG, abs=0.05)

    # Blind, not a second bore: material stands above the socket's floor.
    assert not mesh.contains(np.array([[centre[0], centre[1], 1.0]]))[0]
    assert mesh.contains(np.array([[centre[0], centre[1], SOCKET_DEPTH + 1.0]]))[0]

    # And the wall it leaves behind must stay printable.
    wall = BARREL_D / 2 - np.hypot(socket[:, 0], socket[:, 1]).max()
    assert wall >= 1.2, f"{plate} socket leaves only {wall:.4f} mm of wall"


# ---------------------------------------------------------------------------
# The clearance dial
# ---------------------------------------------------------------------------


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_the_clearance_dial_reaches_the_geometry(
    trimesh_module, openscad_binary, tmp_path
):
    """
    -D key_clearance_mm=0.3 must actually change the pocket. It would not if
    the parameter were preset-owned: a preset-owned key silently ignores -D.
    """
    import numpy as np

    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "v2_c030",
        {"plate_type": "Embossing Plate", "key_clearance_mm": 0.3},
    )
    mesh = _load(trimesh_module, stl_path, output)

    length, width = KEYS["Embossing Plate"][0]
    loop = _hole_loop(mesh, BOTTOM_PROBE_Z)
    assert np.abs(loop[:, 0]).max() == pytest.approx((width + 2 * 0.3) / 2, abs=0.02)
    assert _polygon_area(loop) == pytest.approx(
        _rounded_rect_area(length, width, 0.3), abs=0.5
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_an_out_of_range_clearance_stops_the_render(openscad_binary, tmp_path):
    """0.6 is past the 0.5 maximum: the assert fires and no STL is written."""
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "v2_c060",
        {"plate_type": "Embossing Plate", "key_clearance_mm": 0.6},
    )
    assert not stl_path.exists(), "an out-of-range clearance still wrote an STL"
    assert "key_clearance_mm must be between 0 and 0.5 mm." in output


# ---------------------------------------------------------------------------
# The console notes
# ---------------------------------------------------------------------------


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_the_size_note_speaks_only_off_size_and_never_as_a_warning(
    openscad_binary, tmp_path
):
    """
    D-V15: the size is a WARNING, never a rejection - and it must say NOTE:,
    because scripts/scad-check.ps1 fails the build on the token WARNING:.
    """
    _, at_preset, _ = _render(
        openscad_binary, tmp_path, "v2_size_ok", {"plate_type": "Embossing Plate"}
    )
    assert SIZE_NOTE_START not in at_preset, "the size note fired at the preset size"
    assert PROTOTYPE_NOTE_START in at_preset, "the prototype note must always speak"

    stl_path, off_size, _ = _render(
        openscad_binary,
        tmp_path,
        "v2_size_off",
        {
            "plate_type": "Embossing Plate",
            "paper_thickness_preset": "Custom",
            # 30.5 is the off-size value because it is NOT the preset. It
            # was the preset until 2026-08-30, when the barrel walked back
            # to Version 1's 30.8 and the two numbers swapped roles.
            "cylinder_diameter_mm": 30.5,
        },
    )
    assert SIZE_NOTE_START in off_size, f"no size note at 30.5 mm:\n{off_size[:600]}"
    assert "WARNING:" not in off_size, "the size note must never use the WARNING: token"
    assert stl_path.exists(), (
        "an off-size cylinder must still render - it is a warning, not a gate"
    )


# ---------------------------------------------------------------------------
# Source guards — these run everywhere, with or without OpenSCAD
# ---------------------------------------------------------------------------


def test_the_version2_file_is_self_contained(source_text):
    """
    No include/use/import directive, so the one file serves desktop and
    MakerWorld alike.

    Comments are stripped first: the file explains what it inlined by quoting
    `include <presets.scad>;` in prose, and a naive grep matches that.
    """
    code = _strip_comments(source_text)
    assert "include <" not in code
    assert "use <" not in code
    assert "import(" not in code
    assert "// INLINED PRESETS - BEGIN" in source_text
    assert "// INLINED PRESETS - END" in source_text


def test_the_version2_tab_sits_above_the_first_hidden_tab(source_text):
    """Anything below the first /* [Hidden] */ never reaches the Customizer."""
    tab = source_text.index("/* [Version 2 Keyed Cutouts] */")
    hidden = source_text.index("/* [Hidden] */")
    assert tab < hidden, "the Version 2 tab is hidden from the Customizer"
    assert "key_clearance_mm = 0.110; // [0:0.005:0.5]" in source_text


def test_the_clearance_is_never_preset_owned(source_text):
    """
    A preset-owned key silently ignores -D. The clearance is the one dial a
    user tunes per printer, so it must stay out of both tables.
    """
    for table in ("PRESET_04", "PRESET_03"):
        start = source_text.index(f"{table} = [")
        end = source_text.index("];", start)
        body = source_text[start:end]
        assert "key_clearance_mm" not in body, f"{table} must not own the clearance"
        assert '["cylinder_diameter_mm",            30.8]' in body.replace("  ", "  ")
        for dropped in (
            "polygon_cutout_radius_mm",
            "polygon_cutout_points",
            "seam_offset_degrees",
        ):
            assert dropped not in body, f"{table} still carries {dropped}"


def test_version2_has_no_integrated_gears(source_text):
    """
    The gears BETA is Version 1 only (D-V6).

    `gears_on` and GEAR_ARROW_WELD_MM survive as Hidden constants so the shared
    tactile code reads exactly as it does in the Version 1 file, so the pin is
    on the parameter, the module and the assets - not on the identifiers.
    """
    code = _strip_comments(source_text)
    assert "integrated_gears" not in code, "the gears parameter must be gone"
    assert "module gear_set" not in code
    assert "assets/" not in code
    assert "gears_on = false;" in code, "the shared code still reads this flag"


def test_the_text_input_is_four_rows_per_face(source_text):
    """
    Version 2 offers exactly Line_1..4 and Back_Line_1..4 (Brennen 2026-08-31):
    the Version 2 embosser's standard is 4 rows per face, so the file does not
    offer fields its cylinder is not meant to hold. Version 1 keeps its 10.
    """
    assert "_all_lines = [Line_1, Line_2, Line_3, Line_4];" in source_text
    assert (
        "_all_back_lines = [Back_Line_1, Back_Line_2, Back_Line_3, Back_Line_4];"
        in source_text
    )
    code = _strip_comments(source_text)
    assert "Line_5" not in code, "a fifth front line survived the trim"
    assert "Back_Line_5" not in code, "a fifth back line survived the trim"
    assert "grid_rows = 4; // [1:1:4]" in source_text, (
        "the grid_rows slider must stop at the four fields that exist"
    )


def test_the_barrel_preset_is_the_54_mm_card_shelf(source_text):
    """
    30.8 x 54 since 2026-08-31: 1 mm of barrel past each edge of the 52 mm
    card, Version 2's alone - the Version 1 default returned to 52 the same
    day. The dial, both preset tables and the size-note gate must agree, or
    the note contradicts the geometry it describes.
    """
    assert "cylinder_height_mm = 54;" in source_text
    assert len(re.findall(r'\["cylinder_height_mm",\s+54\]', source_text)) == 2
    assert "active_cylinder_height_mm != 54" in source_text
    assert "30.8 mm x 54 mm cylinder" in source_text


def test_no_development_tags_reach_the_public_file(source_text):
    """
    The Customizer shows the comment block sitting directly above a parameter
    as that dial's on-screen description, so internal wording-approval labels
    ("Wording SIGNED OFF ... reword only with his sign-off") leaked into the
    public UI until Brennen caught one on a dial (2026-09-01). Sign-off
    bookkeeping lives in the repos' docs and in these tests' own pins - never
    in the shipped file, visible or not.
    """
    lowered = source_text.lower()
    assert "signed off" not in lowered, "a sign-off label is back in the public file"
    assert "sign-off" not in lowered, (
        "a sign-off instruction is back in the public file"
    )


def test_the_makerworld_copy_is_byte_identical():
    """
    makerworld/ holds the upload file for every listing, so Version 2 keeps a
    copy there beside the Version 1 build (Brennen, 2026-09-01). The file is
    self-contained, so unlike Version 1 there is no flattening step and no
    allowed difference: the copy must be byte-identical to the canonical root
    file, and any drift is a bug in whichever file changed alone.
    """
    copy = (
        PROJECT_ROOT
        / "makerworld"
        / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad"
    )
    assert copy.exists(), "the Version 2 MakerWorld copy is missing"
    assert copy.read_bytes() == V2_FILE.read_bytes(), (
        "makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad has drifted from "
        "the canonical Braille_Cylinder_STL_Generator_EmbosserV2.scad - re-copy "
        "whichever side is stale"
    )


def test_the_version1_files_were_not_touched():
    """Version 2 is a NEW file beside the Version 1 ones, never an edit to them."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", *V1_FILES],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.stdout.strip() == "", (
        f"a Version 1 file has uncommitted changes:\n{result.stdout}"
    )


def test_the_scad_numbers_still_match_the_web_generator(source_text):
    """
    app/geometry/version2.py owns every Version 2 number; this file mirrors
    them. Cross-file default drift is this project's #1 historical bug source.

    Skipped when the web repository is not checked out beside this one - a CI
    job with only this repo cannot see it, and failing there would report a
    problem that does not exist.
    """
    if not WEB_VERSION2.exists():
        pytest.skip(f"the web generator is not checked out at {WEB_VERSION2}")
    web = WEB_VERSION2.read_text(encoding="utf-8")

    def web_number(name):
        match = re.search(rf"^{name}\s*=\s*([0-9.]+)", web, re.MULTILINE)
        assert match, f"{name} not found in version2.py"
        return float(match.group(1))

    def scad_number(name):
        match = re.search(rf"^{name}\s*=\s*([0-9.]+);", source_text, re.MULTILINE)
        assert match, f"{name} not found in the .scad"
        return float(match.group(1))

    for scad_name, web_name in (
        ("V2_KEY_CORNER_R", "V2_KEY_CORNER_RADIUS_MM"),
        ("V2_COUNTERSINK_OFFSET", "V2_COUNTERSINK_OFFSET_MM"),
        ("V2_COUNTERSINK_DEPTH", "V2_COUNTERSINK_DEPTH_MM"),
        ("V2_OVERLAP", "V2_OVERLAP_MM"),
        ("V2_ARC_FN", "V2_ARC_SEGMENTS"),
        ("V2_ARROW_COLUMN", "V2_ARROW_COLUMN_DEG"),
    ):
        assert scad_number(scad_name) == web_number(web_name), (
            f"{scad_name} has drifted"
        )

    # The nub, whose numbers live in a dict on the web side.
    nub = re.search(r"V2_NUB\s*=\s*\{(.*?)\}", web, re.DOTALL)
    assert nub, "V2_NUB not found in version2.py"
    for scad_name, key in (
        ("V2_NUB_SIDE", "side"),
        ("V2_NUB_BASE_R", "base_radius"),
        ("V2_NUB_APEX_R", "apex_radius"),
        ("V2_NUB_HEIGHT", "height"),
        ("V2_NUB_TOP_CHAMFER", "top_chamfer"),
        ("V2_NUB_BASE_FLARE", "base_flare"),
    ):
        found = re.search(rf"'{key}':\s*([0-9.]+)", nub.group(1))
        assert found, f"{key} not found in V2_NUB"
        assert scad_number(scad_name) == float(found.group(1)), (
            f"{scad_name} has drifted"
        )

    # The four profiles, [length, width] here against {'length': , 'width': } there.
    for scad_name, web_key in (
        ("V2_KEY_A1", "a1_square_14"),
        ("V2_KEY_A2", "a2_rect_18x10"),
        ("V2_KEY_B1", "b1_rect_16x12"),
        ("V2_KEY_B2", "b2_rect_20x8"),
    ):
        pair = re.search(
            rf"^{scad_name}\s*=\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]",
            source_text,
            re.MULTILINE,
        )
        assert pair, f"{scad_name} not found in the .scad"
        entry = re.search(
            rf"'{web_key}':\s*\{{'length':\s*([0-9.]+),\s*'width':\s*([0-9.]+)\}}", web
        )
        assert entry, f"{web_key} not found in V2_KEY_PROFILES"
        assert (float(pair.group(1)), float(pair.group(2))) == (
            float(entry.group(1)),
            float(entry.group(2)),
        ), f"{scad_name} has drifted from {web_key}"
