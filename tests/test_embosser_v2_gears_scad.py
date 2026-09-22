"""
Embosser Version 2 fixed gears - the FUSED roller renders of
Braille_Cylinder_STL_Generator_EmbosserV2.scad (OpenSCAD parity plan phase O5,
2026-09-21, mirroring the web generator's 2026-09-20 programme sub-plan B).

What this proves about the file the user actually renders:

  * with integrated_gears On, each plate exports as ONE watertight roller
    74 mm tall (gears at z -10..0 and 54..64) with 24 teeth in each band;
  * the barrel is SOLID: no keyed hole, no socket, no nub (D-6);
  * each top gear's anti-rotation notch is filled, so no void is sealed in;
  * the seam channel is still cut, at the same physical angle as without gears;
  * a barrel the gears cannot fit is REFUSED with the web generator's sentence;
  * with integrated_gears Off the geometry is exactly the pre-gears file's
    (a recorded signature, see tests/fixtures/version2_gears/README.md);
  * every gear number in the .scad still equals the web generator's.

Judged by OUTPUT TEXT and FILE EXISTENCE, never by an exit code - the rule
test_gear_rollers_scad.py follows, because one test asserts on a render that
is SUPPOSED to fail.

Render tests skip when no OpenSCAD binary is available; the source guards run
everywhere, including the no-OpenSCAD CI job.

License: PolyForm Noncommercial 1.0.0
"""

import json
import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_embosser_v2_scad import (  # noqa: E402
    V2_FILE,
    WEB_VERSION2,
    _load,
    _render,
    _strip_comments,
)
from test_seam_channel_scad import (  # noqa: E402
    BASELINE_FLAGS,
    _groove_cap_angles_at,
    _signature,
)
from test_seam_channel_scad import _render as _render_binary  # noqa: E402
from test_text_too_long import _resolve_openscad_path  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
OFF_SIGNATURE = (
    PROJECT_ROOT / "tests" / "fixtures" / "version2_gears" / "gears_off_signature.json"
)
WEB_GEARS = WEB_VERSION2.parent / "gears.py"

TIP_RADIUS_MM = 16.1093702290795
TOOTH_COUNT = 24
BARREL_H = 54.0
GEAR_BANDS = ((-10.0, 0.0), (BARREL_H, BARREL_H + 10.0))
ROLLER_Z_MIN = -10.0
ROLLER_Z_MAX = BARREL_H + 10.0
XY_LIMIT_MM = 16.110
BOUNDS_TOL_MM = 0.001

# The web generator's S-G1 sentence (app/geometry/gears.py, reference_roller_message
# for version 2). Pinned here, and checked against that file when it is beside us.
SIZE_MESSAGE = (
    "Fixed gears for the Version 2 embosser fit only a 30.8 mm x 54 mm cylinder."
)
HOUSING_NOTE = (
    "NOTE: Version 2 fixed gears fit only the Version 2 fixed-gear housing. "
    "The standard Version 2 housing takes the standard keyed cylinders."
)

# The notch fill, app/geometry/version2.py: V2_NOTCH_FILL_*_MM and the two
# top-gear notches of V2_GEAR_ANTIROT (a1_notch, b1_notch; gear v7.2 = v8).
NOTCH_FILL_GROWTH = 0.05
NOTCH_FILL_MAX_RADIUS = 13.95
NOTCH_FILL_OVERLAP = 0.05
NOTCH_DEPTH = 3.15
B1_NOTCH = (9.80, 13.10, 1.65)  # inner radius, outer radius, half width
A1_NOTCH_WEB = (9.9091, 13.8525, 2.2768)  # MEASURED off the gear
# The .scad derives A's notch from the nominal nub (V2_NUB_*) inset by
# V2_GEAR_TRIANGLE_INSET, so it differs from the measured web numbers by float
# noise, never more than this.
A1_DERIVED_TOL = 0.01
NUB_SIDE = 5.073158
NUB_BASE_R = 9.754087
NUB_APEX_R = 14.147487
TRIANGLE_INSET = 0.15
V1_OPERATING_AXIS_DISTANCE_MM = 32.0473
GROOVE_DEG = {"Embossing Plate": 181.67, "Counter Plate": 178.33}

# Probes on the 180 degree column inside each top gear's notch window
# (r 9.9..13.85 on A, 9.8..13.1 on B; z 54..57.15 in the base-at-zero frame).
NOTCH_PROBES = [
    [-11.0, 0.0, 54.2],
    [-12.0, 0.0, 55.5],
    [-11.0, 0.0, 57.0],
    [-10.5, 0.0, 56.0],
    [-12.5, 0.0, 54.5],
]
# The old keyed hole (r <= 10.7 at every height) and the socket (bottom 3.15 mm)
# and the nub (above the top face) - every one must be solid material now.
SOLID_PROBES = [
    [0.0, 0.0, 27.0],
    [10.0, 0.0, 27.0],
    [-10.0, 0.0, 27.0],
    [0.0, 10.0, 27.0],
    [0.0, -10.0, 27.0],
    [0.0, 0.0, 8.0],
    [0.0, 0.0, 46.0],
    [-7.0, 0.0, 8.0],
    [-7.0, 0.0, 46.0],
]


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
    pytest.skip("OpenSCAD not available for the Version 2 gear render tests")


@pytest.fixture(scope="module")
def source_text():
    return V2_FILE.read_text(encoding="utf-8")


def _tooth_clusters(mesh, z_low, z_high):
    import numpy as np

    band = mesh.vertices[(mesh.vertices[:, 2] > z_low) & (mesh.vertices[:, 2] < z_high)]
    radius = np.hypot(band[:, 0], band[:, 1])
    tips = band[radius > (TIP_RADIUS_MM - 0.05)]
    if len(tips) == 0:
        return 0
    angles = np.sort(np.degrees(np.arctan2(tips[:, 1], tips[:, 0])) % 360.0)
    gaps = np.diff(np.concatenate([angles, [angles[0] + 360.0]]))
    return max(1, int((gaps > 2.0).sum()))


def _scad_number(text, name):
    match = re.search(rf"^{name}\s*=\s*([0-9.]+);", text, re.MULTILINE)
    assert match, f"{name} not found in the .scad"
    return float(match.group(1))


def _fused(openscad_binary, tmp_path, plate, **extra):
    name = "fused_" + plate.split()[0].lower()
    defines = {"integrated_gears": "On", "plate_type": plate}
    defines.update(extra)
    return _render(openscad_binary, tmp_path, name, defines)


# ---------------------------------------------------------------------------
# Renders
# ---------------------------------------------------------------------------


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_fused_plate_is_one_watertight_roller(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """74 mm tall, one solid, gears at both ends, no enclosed cavity (D-6)."""
    import numpy as np

    stl_path, output, _ = _fused(openscad_binary, tmp_path, plate)
    mesh = _load(trimesh_module, stl_path, output)
    assert HOUSING_NOTE in output, "the housing note must be said out loud"

    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 1, f"{len(bodies)} bodies - a sealed void or a loose gear"
    assert mesh.is_watertight
    assert all(body.volume > 0 for body in bodies)

    low, high = mesh.bounds
    assert low[2] == pytest.approx(ROLLER_Z_MIN, abs=BOUNDS_TOL_MM)
    assert high[2] == pytest.approx(ROLLER_Z_MAX, abs=BOUNDS_TOL_MM)

    # The tip-radius envelope belongs to the GEAR BANDS; over the barrel the
    # raised dots stand further out than the teeth (test_gear_rollers_scad).
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
def test_the_barrel_is_solid_and_the_notch_is_filled(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """
    No keyed hole, no socket (the axis is solid material at every height), and
    the top gear's notch window on the arrow column is solid too - the fill
    that stops a solid barrel face sealing the notch into an undrainable void.
    """
    import numpy as np

    stl_path, output, _ = _fused(openscad_binary, tmp_path, plate)
    mesh = _load(trimesh_module, stl_path, output)
    assert mesh.contains(np.array(SOLID_PROBES)).all(), (
        "the keyed hole or socket is back"
    )
    assert mesh.contains(np.array(NOTCH_PROBES)).all(), "the top notch is open"


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_the_groove_survives_the_fused_roller(
    trimesh_module, openscad_binary, tmp_path, plate
):
    """The channel is cut before the gears join, at the same physical angle."""
    stl_path, output, _ = _fused(openscad_binary, tmp_path, plate)
    _load(trimesh_module, stl_path, output)
    assert "NOTE: The seam channel" not in output
    angles = _groove_cap_angles_at(trimesh_module, stl_path, BARREL_H)
    expected = GROOVE_DEG[plate]
    assert angles and all(abs(a - expected) < 0.05 for a in angles), (
        f"groove at {angles}, expected {expected}"
    )


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize(
    ("defines", "label"),
    [
        ({"cylinder_height_mm": 52}, "the 52 mm Version 1 barrel"),
        ({"cylinder_diameter_mm": 30.5}, "a 30.5 mm barrel"),
    ],
)
def test_a_cylinder_the_gears_cannot_fit_is_refused(
    openscad_binary, tmp_path, defines, label
):
    """
    The size assert must FIRE with the web generator's sentence, and no STL may
    be written. The gears are baked at fixed heights: a 52 mm barrel would
    export as loose bodies. Unlike the keyed cylinder's soft size NOTE, this is
    a gate - the same rule the web generator applies (S-G1).
    """
    stl_path, output, _ = _fused(
        openscad_binary,
        tmp_path,
        "Embossing Plate",
        paper_thickness_preset="Custom",
        **defines,
    )
    assert "ERROR:" in output, f"the assert did not fire for {label}:\n{output[:800]}"
    assert SIZE_MESSAGE in output, (
        f"the assert fired with the wrong wording for {label}"
    )
    assert not stl_path.exists(), f"an STL was written despite {label}"


@pytest.mark.requires_openscad
@pytest.mark.slow
@pytest.mark.parametrize("plate", ["Embossing Plate", "Counter Plate"])
def test_gears_off_is_the_pre_gears_geometry(openscad_binary, tmp_path, plate):
    """
    The default render (gears Off, channel On) matches the signature recorded
    from the file as committed BEFORE the gear switch existed (phase O2), so
    turning the feature off is exactly the old file - the "off is identical"
    contract the seam channel keeps with tests/fixtures/seam_channel/.
    """
    recorded = json.loads(OFF_SIGNATURE.read_text(encoding="utf-8"))[plate]
    stl_path = tmp_path / "plate.stl"
    output = _render_binary(
        openscad_binary, V2_FILE, stl_path, {"plate_type": plate}, flags=BASELINE_FLAGS
    )
    assert "ERROR:" not in output and "WARNING:" not in output, output[:800]
    assert stl_path.exists()
    assert _signature(stl_path.read_bytes()) == recorded["signature"], (
        "the gears-Off Version 2 render no longer matches the pre-gears file"
    )


# ---------------------------------------------------------------------------
# Source guards - these run everywhere, with or without OpenSCAD
# ---------------------------------------------------------------------------


def test_the_switch_is_declared_off_above_the_first_hidden_tab(source_text):
    """A Customizer dial, Off by default, described without development labels."""
    assert "/* [Integrated Gears] */" in source_text, "the section header is missing"
    assert (
        "BETA" not in source_text.split("/* [Integrated Gears] */")[1].split("/* [")[0]
    )
    declaration = 'integrated_gears = "Off"; // [Off, On]'
    assert declaration in source_text
    assert source_text.index(declaration) < source_text.index("/* [Hidden] */"), (
        "the gear switch is hidden from the Customizer"
    )
    description = source_text.split(declaration)[0].split("/* [Integrated Gears] */")[1]
    assert description.lstrip().startswith("// Adds the Version 2 drive gears"), (
        description
    )
    lowered = description.lower()
    for tag in ("draft", "sign", "brennen"):
        assert tag not in lowered, f"{tag!r} reaches the Customizer description"
    assert "assets/v2_gears_a.stl and assets/v2_gears_b.stl" in description


def test_the_gate_is_normalised_and_not_preset_owned(source_text):
    """
    Read like ds_on (On/on), and never a preset-owned key: a preset-owned key
    silently ignores -D, and the fused roller must be reachable headlessly.
    """
    code = _strip_comments(source_text)
    assert (
        'gears_on = (integrated_gears == "On") || (integrated_gears == "on");' in code
    )
    assert "gears_on = false;" not in code, "the D-V6 constant is back"
    for table in ("PRESET_04", "PRESET_03"):
        start = source_text.index(f"{table} = [")
        end = source_text.index("];", start)
        assert "integrated_gears" not in source_text[start:end], (
            f"{table} owns the switch"
        )


def test_the_fused_shell_keeps_only_the_seam_channel(source_text):
    """
    Inside cylinder_shell_v2 the channel is cut unconditionally and FIRST; the
    keyed halves, the four mouths and the socket sit behind `if (!gears_on)`.
    """
    code = _strip_comments(source_text)
    shell = code.split("module cylinder_shell_v2(")[1].split("\nmodule ")[0]
    gate = shell.index("if (!gears_on) {")
    assert shell.index("seam_channel_cut(channel_theta_deg)") < gate
    for cut in ("keyed_half_cutout(", "mouth_countersink(", "bottom_key_socket("):
        assert shell.index(cut) > gate, f"{cut} is cut even while the gears are on"


def test_the_gears_join_the_raised_stage_and_the_nub_is_gated(source_text):
    """
    In both plate modules the gear set follows the shell inside the union and
    the nub only exists while the gears are off - gear A1 / B1 is already on.
    """
    code = _strip_comments(source_text)
    for module, flag in (
        ("cylinder_emboss_plate", "true"),
        ("cylinder_counter_plate", "false"),
    ):
        body = code.split(f"module {module}()")[1].split("\nmodule ")[0]
        shell = body.index("cylinder_shell_v2(emboss = " + flag)
        gears = body.index(f"gear_set_v2(emboss = {flag});")
        nub = body.index(f"top_key_nub(active_cylinder_height_mm / 2, {flag});")
        assert shell < gears < nub, f"{module}: order must be shell, gears, nub"
        assert "if (gears_on) {" in body[shell:gears]
        assert "if (!gears_on) {" in body[gears:nub]


def test_gear_set_v2_imports_the_version2_assets_with_rings_and_fill(source_text):
    """The desktop assets, the two hidden weld rings and the notch fill, as in V1."""
    code = _strip_comments(source_text)
    module = code.split("module gear_set_v2(emboss = is_emboss_plate)")[1].split(
        "\nmodule "
    )[0]
    assert (
        'import(emboss ? "assets/v2_gears_a.stl" : "assets/v2_gears_b.stl");' in module
    )
    assert code.count("import(") == 1, "the gear assets are the file's only import"
    assert "notch_fill(emboss);" in module
    assert "GEAR_WELD_RING_R_OUT" in module and "GEAR_WELD_RING_R_IN" in module
    for asset in ("v2_gears_a.stl", "v2_gears_b.stl"):
        assert (PROJECT_ROOT / "assets" / asset).exists(), f"assets/{asset} is missing"
    v1 = V1_FILE.read_text(encoding="utf-8")
    for name in (
        "GEAR_WELD_RING_R_IN",
        "GEAR_WELD_RING_R_OUT",
        "GEAR_WELD_RING_H",
        "GEAR_ARROW_WELD_MM",
    ):
        assert _scad_number(source_text, name) == _scad_number(v1, name), (
            f"{name} differs from V1"
        )


def test_the_notch_fill_is_an_exact_parallel_curve_of_the_raw_notch(source_text):
    """offset(r = growth) of the SAME outlines the nub and the socket use - never a mitre."""
    code = _strip_comments(source_text)
    fill = code.split("module notch_fill_2d(emboss)")[1].split("\nmodule ")[0]
    assert "offset(r = V2_NOTCH_FILL_GROWTH, $fn = V2_ARC_FN)" in fill
    assert "offset(delta" not in fill
    assert "nub_2d(V2_GEAR_TRIANGLE_INSET)" in fill
    assert "radial_rect_2d(V2_ANTIROT_B1_NOTCH, 0)" in fill
    prism = code.split("module notch_fill(emboss)")[1].split("\nmodule ")[0]
    assert "half_h - V2_NOTCH_FILL_OVERLAP" in prism
    assert "V2_GEAR_NOTCH_DEPTH + 2 * V2_NOTCH_FILL_OVERLAP" in prism


def test_the_fill_reach_stays_under_the_cap():
    """
    The analytic reach of both fills, as the .scad's v2_notch_fill_reach()
    computes it: A's inset apex plus the growth, B's grown far corner.
    """
    half_apex = math.atan((NUB_SIDE / 2) / (NUB_APEX_R - NUB_BASE_R))
    reach_a = NUB_APEX_R - TRIANGLE_INSET / math.sin(half_apex) + NOTCH_FILL_GROWTH
    reach_b = math.hypot(B1_NOTCH[1], B1_NOTCH[2]) + NOTCH_FILL_GROWTH
    assert reach_a <= NOTCH_FILL_MAX_RADIUS and reach_b <= NOTCH_FILL_MAX_RADIUS
    # The web generator's notch_fill_outline() reaches 13.9025 (A, from the
    # MEASURED apex 13.8525) and 13.2535 (B).
    assert reach_a == pytest.approx(
        A1_NOTCH_WEB[1] + NOTCH_FILL_GROWTH, abs=A1_DERIVED_TOL
    )
    assert reach_b == pytest.approx(13.2535, abs=1e-4)
    # And the cap itself stays clear of the mating tip circle.
    assert NOTCH_FILL_MAX_RADIUS < V1_OPERATING_AXIS_DISTANCE_MM - TIP_RADIUS_MM


def test_the_size_gate_and_the_housing_note(source_text):
    """A hard stop with the web sentence; the housing note as NOTE:, gear mode only."""
    code = _strip_comments(source_text)
    assert f'"{SIZE_MESSAGE}"' in code
    gate = code.split("assert(!gears_on")[1].split(";")[0]
    assert "V2_GEAR_BARREL_HEIGHT_MM" in gate and "V2_GEAR_BARREL_DIAMETER_MM" in gate
    assert "V2_GEAR_SIZE_TOLERANCE_MM" in gate
    assert _scad_number(source_text, "V2_GEAR_BARREL_DIAMETER_MM") == 30.8
    assert _scad_number(source_text, "V2_GEAR_BARREL_HEIGHT_MM") == 54
    assert _scad_number(source_text, "V2_GEAR_SIZE_TOLERANCE_MM") == 0.001
    note = code.split("if (gears_on) {")[1].split("}")[0]
    assert f'echo("{HOUSING_NOTE}");' in note
    assert "WARNING:" not in HOUSING_NOTE


def test_the_tactile_wall_guard_is_off_in_gear_mode(source_text):
    """It measures the wall to the keyed hole, which the fused roller has not got."""
    code = _strip_comments(source_text)
    assert "tactile_seam_wall_too_thin = tactile_on && !gears_on" in code


def test_the_gear_numbers_still_match_the_web_generator(source_text):
    """
    app/geometry/version2.py and gears.py own every fixed-gear number; the
    .scad mirrors them. Skipped when the web repository is not checked out
    beside this one (a CI job with only this repo cannot see it).
    """
    if not WEB_VERSION2.exists() or not WEB_GEARS.exists():
        pytest.skip(f"the web generator is not checked out at {WEB_VERSION2.parent}")
    web = WEB_VERSION2.read_text(encoding="utf-8")
    gears = WEB_GEARS.read_text(encoding="utf-8")

    def web_number(name):
        match = re.search(rf"^{name}\s*=\s*([0-9.]+)", web, re.MULTILINE)
        assert match, f"{name} not found in version2.py"
        return float(match.group(1))

    def web_notch(key, field):
        block = web.split(f"'{key}': {{")[1].split("}")[0]
        match = re.search(rf"'{field}':\s*([0-9.]+)", block)
        assert match, f"{key}.{field} not found in version2.py"
        return float(match.group(1))

    for scad_name, web_name in (
        ("V2_NOTCH_FILL_GROWTH", "V2_NOTCH_FILL_GROWTH_MM"),
        ("V2_NOTCH_FILL_MAX_RADIUS", "V2_NOTCH_FILL_MAX_RADIUS_MM"),
        ("V2_NOTCH_FILL_OVERLAP", "V2_NOTCH_FILL_OVERLAP_MM"),
        ("V1_OPERATING_AXIS_DISTANCE_MM", "V1_OPERATING_AXIS_DISTANCE_MM"),
        ("GEAR_TIP_RADIUS_MM", "GEAR_TIP_RADIUS_MM"),
        ("V2_GEAR_BARREL_DIAMETER_MM", "V2_BARREL_DIAMETER_MM"),
        ("V2_GEAR_BARREL_HEIGHT_MM", "V2_BARREL_HEIGHT_MM"),
    ):
        assert _scad_number(source_text, scad_name) == web_number(web_name), (
            f"{scad_name} = {_scad_number(source_text, scad_name)} in the .scad, "
            f"{web_name} = {web_number(web_name)} in the web generator"
        )
    assert _scad_number(source_text, "V2_GEAR_NOTCH_DEPTH") == web_notch(
        "a1_notch", "depth"
    )
    assert _scad_number(source_text, "V2_GEAR_NOTCH_DEPTH") == web_notch(
        "b1_notch", "depth"
    )
    b1 = re.search(
        r"^V2_ANTIROT_B1_NOTCH = \[([0-9., ]+)\];", source_text, re.MULTILINE
    )
    assert b1, "V2_ANTIROT_B1_NOTCH not found in the .scad"
    assert tuple(float(v) for v in b1.group(1).split(",")) == (
        web_notch("b1_notch", "inner_radius"),
        web_notch("b1_notch", "outer_radius"),
        web_notch("b1_notch", "half_width"),
    )
    # A's notch is derived here and measured there: the same triangle to 5 um.
    half_apex = math.atan((NUB_SIDE / 2) / (NUB_APEX_R - NUB_BASE_R))
    derived_apex = NUB_APEX_R - TRIANGLE_INSET / math.sin(half_apex)
    derived_base = NUB_BASE_R + TRIANGLE_INSET
    assert derived_apex == pytest.approx(
        web_notch("a1_notch", "outer_radius"), abs=A1_DERIVED_TOL
    )
    assert derived_base == pytest.approx(
        web_notch("a1_notch", "inner_radius"), abs=A1_DERIVED_TOL
    )
    assert "'Fixed gears for the Version 2 embosser fit only a '" in gears
