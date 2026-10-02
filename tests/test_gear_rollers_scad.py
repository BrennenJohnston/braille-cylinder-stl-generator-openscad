"""
Integrated gears — the one-piece roller, rendered.

With ``integrated_gears = "On"`` a plate stops being a bare barrel and becomes a
72 mm roller: the vendored gear pair is unioned in at both ends, two hidden weld
rings straddle the interfaces, and the barrel is forced solid. The gears
themselves are replica meshes checked by ``tests/test_gear_assets.py``; what is
checked HERE is what the .scad does with them.

Three things are worth stating about why these particular assertions exist:

* **One body, and no negative-volume body.** The gears are baked at fixed
  heights and do not move with the barrel, so a wrong cylinder size does not
  merely look different - it comes apart. A negative volume is an enclosed void,
  which is what a hollowed barrel plus the weld rings produces; the web
  generator shipped exactly that bug before it was caught, and D-2 exists to
  prevent it.
* **Solid at the DEFAULTS.** The cutout radius defaults to 13 mm, so the
  interesting case is not "does force_solid work when asked" but "is the barrel
  solid on the shipped settings", which is what a user actually renders.
* **The size assert must FIRE.** OpenSCAD cannot test whether an imported file
  exists, so the assert is the only guard between a user and a broken part.
  A test that only proves the good case would not notice if it stopped working.

Render tests skip when no OpenSCAD binary is available; the source guards run
everywhere, including the no-OpenSCAD CI job.

License: PolyForm Noncommercial 1.0.0
"""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
MAKERWORLD_FILE = (
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad"
)

# The reference roller (assets/GEARS_PROVENANCE.json, and the web generator's
# app/geometry/gears.py).
TIP_RADIUS_MM = 16.1093702290795
TOOTH_COUNT = 24
GEAR_BANDS = ((-10.0, 0.0), (52.0, 62.0))
ROLLER_Z_MIN = -10.0
ROLLER_Z_MAX = 62.0
XY_LIMIT_MM = 16.110
BOUNDS_TOL_MM = 0.001

# The signed S7 sentence. The assert must quote it, so a user meets the same
# words here and in the web app.
SIZE_MESSAGE = "Integrated gears are matched to the reference roller and only fit a 30.8 mm x 52 mm cylinder."


@pytest.fixture(scope="module")
def trimesh_module():
    return pytest.importorskip("trimesh")


@pytest.fixture(scope="module")
def openscad_binary():
    """
    The console wrapper, driven directly.

    Not OpenSCADRunner here: these tests need to assert on a render that FAILS
    (the size assert), and they pass `-D name="value"` strings whose quotes
    PowerShell would strip - a mangled define is parsed as code appended past
    EOF and reported as a syntax error on a line that does not exist.
    """
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        # The .com wrapper waits and prints; the .exe detaches.
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the gear render tests")


def _render(binary, tmp_path, name, defines, scad_file=SCAD_FILE):
    """Render once. Returns (stl_path, combined output, returncode)."""
    stl_path = tmp_path / f"{name}.stl"
    command = [str(binary), "--hardwarnings", "--check-parameter-ranges=true"]
    # One plate unless a test asks for the pair: the file's default renders both.
    defines = {"render_both_plates": "Off", **defines}
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(scad_file)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=300, cwd=PROJECT_ROOT
    )
    return (
        stl_path,
        (result.stdout or "") + "\n" + (result.stderr or ""),
        result.returncode,
    )


def _load_roller(trimesh_module, stl_path, output):
    """Judge by output text and file existence, never by an exit code."""
    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    mesh = trimesh_module.load(str(stl_path), file_type="stl", force="mesh")
    mesh.merge_vertices()
    return mesh


def _tooth_clusters(mesh, z_low, z_high):
    """Teeth in the band, counted in a 1 mm slice at its mid-plane (the chevron apex)."""
    import numpy as np

    z_mid = (z_low + z_high) / 2.0
    band = mesh.vertices[np.abs(mesh.vertices[:, 2] - z_mid) <= 0.5]
    radius = np.hypot(band[:, 0], band[:, 1])
    tips = band[radius > (TIP_RADIUS_MM - 0.05)]
    if len(tips) == 0:
        return 0
    angles = np.sort(np.degrees(np.arctan2(tips[:, 1], tips[:, 0])) % 360.0)
    gaps = np.diff(np.concatenate([angles, [angles[0] + 360.0]]))
    return max(1, int((gaps > 5.0).sum()))


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_geared_plate_is_one_watertight_roller(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """72 mm tall, one solid, gears at both ends, no enclosed cavity."""
    name = "geared_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"integrated_gears": "On", "plate_type": plate}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)

    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 1
    assert mesh.is_watertight
    # A negative volume is an enclosed void - the failure D-2 exists to prevent.
    assert all(body.volume > 0 for body in bodies)

    low, high = mesh.bounds
    assert low[2] == pytest.approx(ROLLER_Z_MIN, abs=BOUNDS_TOL_MM)
    assert high[2] == pytest.approx(ROLLER_Z_MAX, abs=BOUNDS_TOL_MM)

    # The tip-radius envelope belongs to the GEAR BANDS, not to the whole part:
    # over the barrel the raised braille dots stand further out than the teeth
    # do (15.4 mm barrel + a ~1 mm dot reaches 16.39, past the 16.109 tips).
    # What matters here is that the gears arrived undistorted.
    import numpy as np

    for z_low, z_high in GEAR_BANDS:
        band = mesh.vertices[
            (mesh.vertices[:, 2] > z_low + 0.5) & (mesh.vertices[:, 2] < z_high - 0.5)
        ]
        assert len(band) > 0
        assert float(np.hypot(band[:, 0], band[:, 1]).max()) <= XY_LIMIT_MM
        assert _tooth_clusters(mesh, z_low + 1.0, z_high - 1.0) == TOOTH_COUNT


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_the_barrel_is_solid_in_gear_mode(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    Decision D-2, probed at the DEFAULTS - where the cutout radius is 13 mm, so
    this is the case a user actually renders. A point at r 10, mid-height, must
    be inside solid material.
    """
    import numpy as np

    name = "solid_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"integrated_gears": "On", "plate_type": plate}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)

    probes = np.array(
        [[10.0, 0.0, 26.0], [0.0, 10.0, 26.0], [-10.0, 0.0, 26.0], [0.0, -10.0, 26.0]]
    )
    assert mesh.contains(probes).all()

    # And the note is said out loud, because the user HAD a cutout set.
    assert "polygonal cutout is not used while integrated gears are on" in output


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_gears_off_leaves_the_cutout_alone(trimesh_module, openscad_binary, tmp_path):
    """
    The toggle-off control for the test above: with gears off the same probe
    must be in AIR, because the polygonal cutout is still cut.
    """
    import numpy as np

    stl_path, output, _ = _render(
        openscad_binary, tmp_path, "plain", {"plate_type": "Embossing Plate"}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)

    probes = np.array([[10.0, 0.0, 26.0], [0.0, 10.0, 26.0]])
    assert not mesh.contains(probes).any()
    assert mesh.bounds[0][2] == pytest.approx(0.0, abs=BOUNDS_TOL_MM)
    assert mesh.bounds[1][2] == pytest.approx(52.0, abs=BOUNDS_TOL_MM)
    assert "polygonal cutout is not used" not in output


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize(
    "defines,label",
    [
        ({"cylinder_height_mm": 45}, "a barrel 7 mm short"),
        ({"cylinder_height_mm": 62}, "a barrel 10 mm tall"),
        ({"cylinder_diameter_mm": 30.75}, "the schema-default diameter"),
    ],
)
def test_a_cylinder_the_gears_cannot_fit_is_refused(
    openscad_binary, tmp_path, defines, label
):
    """
    The size assert must FIRE, and no STL may be written.

    The gears do not move with the barrel: 45 mm would export as loose pieces
    and 62 mm would swallow the teeth. The diameter never breaks the union but
    it sets the nip, so it is gated too.
    """
    params = {"integrated_gears": "On", "paper_thickness_preset": "Custom"}
    params.update(defines)
    stl_path, output, _ = _render(openscad_binary, tmp_path, "refused", params)

    assert "ERROR:" in output, f"the assert did not fire for {label}:\n{output[:800]}"
    assert SIZE_MESSAGE in output, (
        f"the assert fired with the wrong wording for {label}"
    )
    assert not stl_path.exists(), f"an STL was written despite {label}"


@pytest.mark.requires_openscad
@pytest.mark.slow
def test_an_off_size_cylinder_still_renders_with_gears_off(
    trimesh_module, openscad_binary, tmp_path
):
    """The gate is gear-mode only: the same size renders fine without gears."""
    stl_path, output, _ = _render(
        openscad_binary,
        tmp_path,
        "offsize_plain",
        {"paper_thickness_preset": "Custom", "cylinder_height_mm": 45},
    )
    mesh = _load_roller(trimesh_module, stl_path, output)
    assert mesh.bounds[1][2] == pytest.approx(45.0, abs=BOUNDS_TOL_MM)


# --- source guards: these run without OpenSCAD ------------------------------


def test_the_gear_parameter_is_not_preset_owned():
    """
    Trap C3: the presets override -D for the keys they own, silently, and the
    render still looks fine. `integrated_gears` must stay out of both tables so
    a headless -D actually reaches it.
    """
    presets = (PROJECT_ROOT / "presets.scad").read_text(encoding="utf-8")
    assert "integrated_gears" not in presets


def test_the_gear_constants_match_the_reference_roller():
    """The .scad's own numbers, against the values every other file uses."""
    source = SCAD_FILE.read_text(encoding="utf-8")
    assert "GEAR_BARREL_DIAMETER_MM = 30.8;" in source
    assert "GEAR_BARREL_HEIGHT_MM = 52;" in source
    assert "GEAR_WELD_RING_R_IN = 8.0;" in source
    assert "GEAR_WELD_RING_R_OUT = 13.0;" in source
    assert "GEAR_WELD_RING_H = 0.1;" in source
    assert "GEAR_ARROW_WELD_MM = 0.005;" in source


def test_the_makerworld_build_hides_the_gear_switch():
    """
    The MakerWorld build carries the same geometry body - the sync guard
    requires it - but ships no assets/ folder, so its Customizer must not offer
    a switch that would render a gearless plate and only a console warning.
    The declaration lives under a Hidden tab there; the desktop build's does
    not.
    """
    makerworld = MAKERWORLD_FILE.read_text(encoding="utf-8")
    canonical = SCAD_FILE.read_text(encoding="utf-8")

    assert 'integrated_gears = "Off"; // [Off, On]' in makerworld
    assert 'integrated_gears = "Off"; // [Off, On]' in canonical

    def tab_above(text: str) -> str:
        head = text[: text.index('integrated_gears = "Off";')]
        return head[head.rindex("/* [") :].splitlines()[0]

    assert tab_above(makerworld) == "/* [Hidden] */"
    assert tab_above(canonical) == "/* [Gears] */"


# ---------------------------------------------------------------------------
# The vent and self-supporting sockets (2026-09-30, Brennen's approved plan;
# the web generator's gears.axis_cut_blocks). Render frame: barrel 0..52, the
# bottom gear's mouth at -10 and its old blind end at -1.5, the top's blind
# end at 53.5 and mouth at 62. The bottom cone's wall is r = 3.68 - z, the
# top's r = 1.01 + (z - 49.33).
# ---------------------------------------------------------------------------

WEB_GEARS = (
    PROJECT_ROOT.parent
    / "braille-cylinder-stl-generator"
    / "app"
    / "geometry"
    / "gears.py"
)
GEAR_ASSETS = {"Embossing Plate": "gears_a.stl", "Counter Plate": "gears_b.stl"}
SOCKET_DEPTH_MM = 8.5
SOCKET_MOUTH_R_MM = 8.0


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_the_geared_roller_is_vented_with_self_supporting_sockets(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """Air on the axis mouth to mouth, both cones' 45 degree walls, the pin socket still open - one body."""
    import numpy as np

    name = "vented_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"integrated_gears": "On", "plate_type": plate}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)
    assert len(mesh.split(only_watertight=False)) == 1

    axis = np.array([[0.0, 0.0, float(z)] for z in range(-9, 62)])
    beside = np.array([[1.5, 0.0, float(z)] for z in range(3, 49)])
    assert not mesh.contains(axis).any(), "the vent is blocked"
    assert mesh.contains(beside).all(), "the barrel beside the vent is gone"
    bottom_air = np.array([[4.7, 0.0, -1.2], [3.5, 0.0, 0.0], [2.0, 0.0, 1.5]])
    bottom_solid = np.array([[5.1, 0.0, -1.2], [3.9, 0.0, 0.0], [2.0, 0.0, 2.5]])
    top_air = np.array([[4.7, 0.0, 53.2], [3.5, 0.0, 52.0], [2.0, 0.0, 50.5]])
    top_solid = np.array([[5.1, 0.0, 53.2], [3.9, 0.0, 52.0], [2.0, 0.0, 49.5]])
    assert not mesh.contains(bottom_air).any(), "the bottom socket still ends flat"
    assert mesh.contains(bottom_solid).all(), "the bottom cone cut too much"
    assert not mesh.contains(top_air).any(), "the top socket still ends flat"
    assert mesh.contains(top_solid).all(), "the top cone cut too much"
    # The pin socket: air just inside the r 7.0 key bore and the taper, solid
    # just outside (the top gear probed below A1's handle-connector slot).
    socket_air = np.array(
        [[6.9, 0.0, -6.0], [5.95, 0.0, -2.4], [6.9, 0.0, 56.0], [5.95, 0.0, 54.4]]
    )
    socket_wall = np.array(
        [[7.1, 0.0, -6.0], [6.25, 0.0, -2.4], [7.1, 0.0, 56.0], [6.25, 0.0, 54.4]]
    )
    assert not mesh.contains(socket_air).any(), "the pin socket is filled"
    assert mesh.contains(socket_wall).all(), "the pin socket's wall moved"


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_the_cut_leaves_the_pin_socket_exactly(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    Brennen's requirement: the key bore and the taper stay EXACTLY as the
    asset has them, because the Version 1 housing pin is a close fit. Points
    sampled on both sockets' mouth chamfer, key bore and taper - everything
    but the flat blind end the cone removes - lie on the render's surface.
    """
    import numpy as np

    name = "pin_socket_" + plate.split()[0].lower()
    stl_path, output, _ = _render(
        openscad_binary, tmp_path, name, {"integrated_gears": "On", "plate_type": plate}
    )
    mesh = _load_roller(trimesh_module, stl_path, output)
    asset = trimesh_module.load(
        str(PROJECT_ROOT / "assets" / GEAR_ASSETS[plate]), file_type="stl", force="mesh"
    )
    centres = asset.triangles_center
    radial = np.hypot(centres[:, 0], centres[:, 1])
    points = []
    for mouth, sign in ((ROLLER_Z_MIN, 1.0), (ROLLER_Z_MAX, -1.0)):
        depth = (centres[:, 2] - mouth) * sign
        socket = (
            (radial < SOCKET_MOUTH_R_MM + 0.05)
            & (depth > 0.0)
            & (depth < SOCKET_DEPTH_MM - 1e-4)
        )
        faces = np.where(socket)[0]
        sampled, _ = trimesh_module.sample.sample_surface_even(
            asset.submesh([faces], append=True), 20000, seed=11
        )
        points.append(sampled)
    points = np.vstack(points)
    assert len(points) > 20000
    _, distances, _ = trimesh_module.proximity.closest_point(mesh, points)
    assert float(distances.max()) < 1e-4


def test_the_axis_cuts_are_the_last_subtraction_on_both_plates():
    """Vent and cones after every union and every recess - the web worker's order - and only with gears."""
    import re

    source = SCAD_FILE.read_text(encoding="utf-8")
    code = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL))
    for module, flag, last_recess in (
        ("cylinder_emboss_plate", "true", "ds_back_recesses();"),
        ("cylinder_counter_plate", "false", "ds_front_recesses();"),
    ):
        body = code.split(f"module {module}()")[1].split("\nmodule ")[0]
        cut = body.index(f"v1_axis_cuts({flag});")
        assert body.index(f"gear_set(emboss = {flag});") < body.index(last_recess) < cut
        assert "if (gears_on) {" in body[body.index(last_recess) : cut]
    cuts = code.split("module v1_axis_cuts(emboss)")[1].split("\nmodule ")[0]
    assert cuts.count("$fn = AXIS_CUT_FN") == 3
    assert "AXIS_CUT_FN = 48;" in code


def test_the_axis_cut_numbers_match_the_web_generator():
    """
    app/geometry/gears.py owns every number; the .scad mirrors them. Skipped
    when the web repository is not checked out beside this one.
    """
    import re

    if not WEB_GEARS.exists():
        pytest.skip(f"the web generator is not checked out at {WEB_GEARS.parent}")
    web = WEB_GEARS.read_text(encoding="utf-8")
    source = SCAD_FILE.read_text(encoding="utf-8")

    def scad_number(name):
        match = re.search(rf"^{name}\s*=\s*([0-9.]+);", source, re.MULTILINE)
        assert match, f"{name} not found in the .scad"
        return float(match.group(1))

    def web_number(name):
        match = re.search(rf"^{name}\s*=\s*([0-9.]+)", web, re.MULTILINE)
        assert match, f"{name} not found in gears.py"
        return float(match.group(1))

    for scad_name, web_name in (
        ("V1_GEAR_BODY_T", "GEAR_BODY_THICKNESS_MM"),
        ("V1_VENT_R", "V1_VENT_RADIUS_MM"),
        ("V1_VENT_OVERSHOOT", "V1_VENT_OVERSHOOT_MM"),
        ("V1_SOCKET_CONE_OVERLAP", "V1_SOCKET_CONE_OVERLAP_MM"),
        ("V1_SOCKET_TAPER_FACET_DIP", "V1_SOCKET_TAPER_FACET_DIP_MM"),
        ("V1_SOCKET_CONE_INSET", "V1_SOCKET_CONE_INSET_MM"),
        ("V1_SOCKET_CONE_VENT_GROWTH", "V1_SOCKET_CONE_VENT_GROWTH_MM"),
    ):
        assert scad_number(scad_name) == web_number(web_name), scad_name

    fields = (
        "mouth_chamfer",
        "bore_radius",
        "taper_start_depth",
        "rim_radius",
        "depth",
    )
    for scad_name, table, key in (
        ("V1_GEAR_SOCKET_A", "V1_GEAR_SOCKET", "positive"),
        ("V1_GEAR_SOCKET_B", "V1_GEAR_SOCKET", "negative"),
        ("V1_TOP_GEAR_SOCKET_A", "V1_TOP_GEAR_SOCKET", "positive"),
        ("V1_TOP_GEAR_SOCKET_B", "V1_TOP_GEAR_SOCKET", "negative"),
    ):
        vector = re.search(rf"^{scad_name} = \[([0-9., ]+)\];", source, re.MULTILINE)
        assert vector, f"{scad_name} not found in the .scad"
        table_text = web.split(f"\n{table} = {{")[1].split("\n}")[0]
        block = table_text.split(f"'{key}': {{")[1].split("}")[0]
        expected = tuple(
            float(re.search(rf"'{field}':\s*([0-9.]+)", block).group(1))
            for field in fields
        )
        assert tuple(float(v) for v in vector.group(1).split(",")) == expected, (
            scad_name
        )
