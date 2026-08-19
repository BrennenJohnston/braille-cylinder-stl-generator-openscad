"""
Double-sided (interpoint) geometry on Cylinder A, the embossing plate.

With ``double_sided = "On"`` the embossing plate gains three things:

1. Tactile indicators, forced. The paired cylinders carry 1:1 recesses right
   where the Visual marker columns would sit, so double-sided always renders the
   raised seam arrows, warns when that overrode a choice, and never draws the
   marker columns.
2. One bowl recess per ACTUAL back-text dot - the seat the opposing cylinder's
   raised back dot drops into. Positions come from ``back_grid_transform()`` in
   the web generator's ``app/geometry/interpoint.py``, which stays authoritative:
   mirror the layout about the seam plane, then take one diagonal interpoint
   step in the ``DS_BACK_DIRECTION`` sense.
3. The Option B footprints (2026-08-16), fixed: raised dots shrink to 1.2 mm
   base / 0.8 mm tall and the bowls are 1.3 mm x 0.5 mm deep, because a raised
   dot and a recess now share one surface.

Two kinds of test live here, following ``tests/test_interpoint_math_scad.py``:

* **Render tests** run OpenSCAD, load the STL with trimesh and probe it. The
  reference model is front ``a b c`` (5 raised dots) and back ``d e f`` (8
  bowls) on the shipped defaults, which is small enough to render in about a
  second. They skip when no OpenSCAD binary is available.
* **Source guards** read the .scad as text and run everywhere, including the
  no-OpenSCAD CI job.

MEASURED, 2026-08-19, OpenSCAD 2026.01.03 Manifold: this repo cuts the 1.3 mm
bowl **0.6693 mm** deep below the nominal cylinder radius. That is NOT the 0.5 mm
``DS_BOWL_DEPTH`` suggests, and it is not meant to be: the bowl's sphere is
centred ON the shell surface, so the cut is a hemisphere of radius ``DS_BOWL_R``
= 0.6725 mm, and the 0.0032 mm shortfall is sphere tessellation (at
``quality_fn`` = 32 the deepest ring sits at 84.375 deg of latitude, reaching
0.6725 * sin(84.375) = 0.66926 mm).

That convention is deliberate, decided 2026-08-19: it matches
``static/workers/csg-worker-manifold.js`` in the web repo, which is the geometry
that has actually been printed and embossed. The web app's own Python renderer,
and this file's SINGLE-SIDED counter plate, both use the other convention -
centre (R - depth) outside the surface, cut exactly the nominal depth - and are
deliberately left alone. Phase 13's cross-validation tolerances cite 0.6693 mm.

License: PolyForm Noncommercial 1.0.0
"""

import math
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
PRESETS_FILE = PROJECT_ROOT / "presets.scad"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import (  # noqa: E402  (shared helpers)
    _resolve_openscad_path,
    _scad_constant,
)

# The reference model. Front "a b c" is 5 raised dots, back "d e f" is 8 bowls -
# both small, both asymmetric, so a mirrored or transposed layout cannot pass by
# accident.
FRONT_TEXT = "⠁⠃⠉"  # dots 1 | 1-2 | 1-4
BACK_TEXT = "⠙⠑⠋"   # dots 1-4-5 | 1-5 | 1-2-4
EXPECTED_FRONT_DOTS = 5
EXPECTED_BACK_BOWLS = 8

# The fixed dot map, [row, col] for dots 1-6. Same literal as DS_DOT_MAP and
# dot_positions in the .scad; written out here so the test derives positions
# independently instead of trusting the file it is checking.
DOT_MAP = [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]]

# The signed-off physical decisions, hardcoded on purpose. Reading these out of
# the .scad would make the position tests self-consistent and blind: flipping
# DS_BACK_DIRECTION would move the geometry AND the expectation together, and
# nothing would fail. These are the numbers a printed pair was checked against.
#   D3, 2026-08-16: +1, the back grid slides toward the END of the line, so its
#   features sit 1.25 mm HIGHER than the front rows and a further step around
#   the cylinder - LEFT of the seam arrow, seen from outside with the top up.
#   D2, 2026-08-16: Option B raised dots are 0.4 + 0.4 = 0.8 mm tall.
BACK_DIRECTION = 1
OPTION_B_DOT_HEIGHT_MM = 0.8

# How close a rendered feature must land to where the maths puts it.
ANGLE_TOL_DEG = 0.05
Z_TOL_MM = 0.01
# Measured bowl depth, mm, and how far it may drift before the number quoted in
# this file's docstring (and in Phase 13's tolerances) stops being true.
MEASURED_BOWL_DEPTH_MM = 0.6693
BOWL_DEPTH_TOL_MM = 0.002


def _preset_value(key):
    """Pull a numeric value out of the shipped 0.4mm preset table."""
    text = PRESETS_FILE.read_text(encoding="utf-8")
    block = text[text.index("PRESET_04 = [") :]
    block = block[: block.index("];")]
    m = re.search(rf'\["{re.escape(key)}",\s*([0-9.+\-]+)\]', block)
    assert m, f"`{key}` is not in the PRESET_04 table"
    return float(m.group(1))


@pytest.fixture(scope="module")
def scad_source():
    return SCAD_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def layout():
    """
    The shipped-default cylinder layout, re-derived from the preset table and
    the sliders rather than copied out of the geometry code under test.
    """
    radius = _preset_value("cylinder_diameter_mm") / 2
    height = _preset_value("cylinder_height_mm")
    cell = _preset_value("cell_spacing")
    line = _preset_value("line_spacing")
    dot = _preset_value("dot_spacing")
    cols = _scad_constant("grid_columns")
    rows = _scad_constant("grid_rows")

    return {
        "radius": radius,
        "height": height,
        "rows": rows,
        "line": line,
        # Double-sided forces tactile, and tactile has no marker columns, so the
        # grid is exactly the text cells.
        "start_angle": -((cols - 1) * cell / radius) / 2,
        "cell_angle": cell / radius,
        "dot_col_off": [-(dot / radius) / 2, +(dot / radius) / 2],
        "dot_row_off": [dot, 0.0, -dot],
        "top_margin": (height - (rows - 1) * line) / 2,
        "offset_x": _scad_constant("interpoint_offset_x_mm"),
        "offset_y": _scad_constant("interpoint_offset_y_mm"),
        "back_dir": BACK_DIRECTION,
        "bowl_dia": _scad_constant("DS_BOWL_DIA"),
        "bowl_depth": _scad_constant("DS_BOWL_DEPTH"),
        "dot_height": OPTION_B_DOT_HEIGHT_MM,
        "arrow_raise": _scad_constant("tactile_indicator_raise"),
        "arrow_length": _scad_constant("tactile_indicator_length"),
    }


def _row_y(layout, row):
    return layout["height"] / 2 - layout["top_margin"] - row * layout["line"]


def _dots_of(char):
    """Unicode braille -> the six 0/1 flags, dot 1 first."""
    pattern = ord(char) - 0x2800
    return [(pattern >> i) & 1 for i in range(6)]


def _front_placements(layout, line, row=0):
    """(planar angle in radians, height in mm) of every raised dot in `line`."""
    out = []
    y_pos = _row_y(layout, row)
    for col, char in enumerate(line):
        col_angle = layout["start_angle"] + col * layout["cell_angle"]
        for i, on in enumerate(_dots_of(char)):
            if not on:
                continue
            row_idx, col_idx = DOT_MAP[i]
            out.append(
                (
                    col_angle + layout["dot_col_off"][col_idx],
                    y_pos + layout["dot_row_off"][row_idx],
                )
            )
    return out


def _back_placements(layout, line, row=0):
    """
    The same walk, moved onto the interpoint grid: mirrored about the seam plane
    (a negated angle, because the grid is centred on 0) plus one diagonal step.
    """
    return [
        (
            -angle + layout["back_dir"] * (layout["offset_x"] / layout["radius"]),
            y + layout["back_dir"] * layout["offset_y"],
        )
        for angle, y in _front_placements(layout, line, row)
    ]


def _ang_diff(a_deg, b_deg):
    """Smallest signed difference between two angles, in degrees."""
    return (a_deg - b_deg + 180.0) % 360.0 - 180.0


@pytest.fixture(scope="module")
def _trimesh():
    try:
        import trimesh
    except ImportError:
        pytest.skip("trimesh is not installed; skipping the double-sided render tests")
    return trimesh


@pytest.fixture(scope="module")
def ds_runner():
    from openscad_runner import OpenSCADNotFoundError, OpenSCADRunner

    try:
        return OpenSCADRunner(openscad_path=_resolve_openscad_path())
    except OpenSCADNotFoundError as exc:
        pytest.skip(f"OpenSCAD not available for the double-sided tests: {exc}")


def _ds_params(**overrides):
    """The reference double-sided model, on the shipped defaults."""
    params = {
        "double_sided": "On",
        "indicator_mode": "Tactile",
        "Line_1": FRONT_TEXT,
        "Line_2": "",
        "Back_Line_1": BACK_TEXT,
    }
    params.update(overrides)
    return params


def _render(ds_runner, tmp_path, params, name):
    """Render once; return (stl_path, combined stdout+stderr)."""
    stl_path = tmp_path / f"{name}.stl"
    result = ds_runner.generate_stl(
        scad_file=SCAD_FILE,
        output_stl=stl_path,
        parameters=params,
        timeout_seconds=180,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.success, (
        f"OpenSCAD failed to render `{name}`\n"
        f"returncode={result.returncode}\n"
        f"output (truncated): {output[:800]}"
    )
    return stl_path, output


class _Features:
    """
    The raised and recessed features of a rendered cylinder, as vertex clusters.

    Everything is measured in the plate's own frame: `theta` degrees around the
    axis, `z` millimetres from the cylinder's mid-height (the module is
    translated up by half its height on the way out, which is undone here).
    """

    def __init__(self, trimesh_module, stl_path, layout):
        import numpy as np

        mesh = trimesh_module.load(stl_path)  # merges duplicate vertices
        v = mesh.vertices
        self.np = np
        self.radius = layout["radius"]
        # The plate is translated up by half its height on the way out. Undo that
        # from the known height, never from the bounding box: a render carrying a
        # warning extrusion is taller than the cylinder.
        self.z_origin = layout["height"] / 2.0
        self.r = np.hypot(v[:, 0], v[:, 1])
        self.theta = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
        self.z = v[:, 2] - self.z_origin
        self.v = v

        # Only the cylinder's own surface: this drops the polygonal bore, the
        # end faces, and the warning text that floats above the top.
        inside = np.abs(self.z) < layout["height"] / 2.0
        band = (self.r > self.radius - 1.0) & (self.r < self.radius + 2.0) & inside
        self.raised = band & (self.r > self.radius + 0.05)
        self.recessed = band & (self.r < self.radius - 0.05)

    def clusters(self, mask, tol=1.0):
        """Single-linkage clusters of the masked vertices, `tol` mm apart."""
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import pdist

        np = self.np
        pts = self.v[mask]
        if len(pts) == 0:
            return []
        labels = fcluster(linkage(pdist(pts), method="single"), tol, criterion="distance")
        out = []
        for label in sorted(set(labels)):
            sel = pts[labels == label]
            r = np.hypot(sel[:, 0], sel[:, 1])
            out.append(
                {
                    "theta": math.degrees(math.atan2(sel[:, 1].mean(), sel[:, 0].mean())),
                    "z": float(sel[:, 2].mean()) - self.z_origin,
                    "r_min": float(r.min()),
                    "r_max": float(r.max()),
                    "n": len(sel),
                }
            )
        return out

    def away_from_seam(self, mask, min_deg=10.0):
        """Drop everything near 180 deg, where the tactile arrows live."""
        return mask & (self.np.abs(self.np.abs(self.theta) - 180.0) > min_deg)


def _match(clusters, expected, label):
    """
    Pair each cluster with the position the maths predicts, one to one.

    Returns the pairs; asserts on count, on any cluster with no match, and on
    any predicted position nothing rendered at.
    """
    assert len(clusters) == len(expected), (
        f"{label}: rendered {len(clusters)} features, the interpoint maths "
        f"predicts {len(expected)}.\n"
        f"rendered: {[(round(c['theta'], 3), round(c['z'], 3)) for c in clusters]}\n"
        f"predicted: {[(round(math.degrees(a), 3), round(y, 3)) for a, y in expected]}"
    )

    unmatched = list(expected)
    pairs = []
    for cluster in clusters:
        hit = None
        for candidate in unmatched:
            angle_deg, y = candidate
            if (
                abs(_ang_diff(cluster["theta"], math.degrees(angle_deg))) <= ANGLE_TOL_DEG
                and abs(cluster["z"] - y) <= Z_TOL_MM
            ):
                hit = candidate
                break
        assert hit is not None, (
            f"{label}: a feature rendered at theta={cluster['theta']:.3f} deg, "
            f"z={cluster['z']:.3f} mm matches no predicted position within "
            f"{ANGLE_TOL_DEG} deg / {Z_TOL_MM} mm.\n"
            f"still unmatched: {[(round(math.degrees(a), 3), round(y, 3)) for a, y in unmatched]}"
        )
        unmatched.remove(hit)
        pairs.append((cluster, hit))

    assert not unmatched, f"{label}: nothing rendered at {unmatched}"
    return pairs


@pytest.fixture(scope="module")
def ds_features(ds_runner, _trimesh, layout, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("double_sided")
    stl_path, output = _render(ds_runner, tmp_path, _ds_params(), "cylinder_a")
    assert "ERROR:" not in output, f"Render reported an error:\n{output[:800]}"
    return _Features(_trimesh, stl_path, layout)


class TestCylinderAGeometry:
    """The reference model: 5 raised front dots, 8 back bowls, 4 seam arrows."""

    def test_raised_front_dots(self, ds_features, layout):
        clusters = ds_features.clusters(ds_features.away_from_seam(ds_features.raised))
        pairs = _match(clusters, _front_placements(layout, FRONT_TEXT), "raised front dots")
        assert len(pairs) == EXPECTED_FRONT_DOTS

    def test_back_bowls_are_one_per_actual_back_dot(self, ds_features, layout):
        """
        1:1 with the back text, never a universal grid. A universal grid would
        put a bowl at all 6 positions of all 13 cells of all 4 rows.
        """
        clusters = ds_features.clusters(ds_features.recessed)
        pairs = _match(clusters, _back_placements(layout, BACK_TEXT), "back bowls")
        assert len(pairs) == EXPECTED_BACK_BOWLS

    def test_back_band_sits_one_axial_step_above_the_front_rows(self, ds_features, layout):
        """
        Every bowl is exactly interpoint_offset_y_mm HIGHER than a front row -
        higher, not lower: that is the D3 sign, confirmed on a printed pair.
        """
        step = BACK_DIRECTION * layout["offset_y"]
        assert step > 0
        front_rows = {round(y, 6) for _, y in _front_placements(layout, FRONT_TEXT)}
        for cluster in ds_features.clusters(ds_features.recessed):
            assert any(
                abs(cluster["z"] - (y + step)) <= Z_TOL_MM for y in front_rows
            ), (
                f"A bowl at z={cluster['z']:.3f} mm is not {step:+.2f} mm above any "
                f"front dot row {sorted(front_rows)}."
            )

    def test_back_grid_is_mirrored_about_the_seam_plane(self, ds_features, layout):
        """
        The front text sits on one side of the grid centre and its mirror image
        on the other. Miss the mirror and the back text would read backwards on
        the paper - the failure no clearance number can catch.
        """
        front = [math.degrees(a) for a, _ in _front_placements(layout, FRONT_TEXT)]
        assert all(a < 0 for a in front), "The reference text must sit on one side of centre."
        for cluster in ds_features.clusters(ds_features.recessed):
            assert 0.0 < cluster["theta"] < 180.0, (
                f"A bowl rendered at theta={cluster['theta']:.3f} deg, on the same side as "
                f"the front dots ({[round(a, 1) for a in front]} deg). The back grid must be "
                "mirrored about the seam plane, which is a negated angle here."
            )

    def test_back_grid_steps_toward_the_end_of_the_line(self, ds_features, layout):
        """
        D3, the sign: +1 slides the back grid toward the END of the line, so each
        bowl sits at a LARGER angle than the bare mirror of its own dot - i.e.
        nearer the 180 deg arrow, and to the viewer's LEFT of it seen from
        outside the cylinder with the top up. Flipping the sign is the first
        thing to try if a printed pair ever crowds the wrong side of the arrow.
        """
        step_deg = math.degrees(layout["offset_x"] / layout["radius"])
        assert step_deg > 0
        mirrored = sorted(-math.degrees(a) for a, _ in _front_placements(layout, BACK_TEXT))
        rendered = sorted(c["theta"] for c in ds_features.clusters(ds_features.recessed))
        for got, bare_mirror in zip(rendered, mirrored):
            assert abs(got - (bare_mirror + step_deg)) <= ANGLE_TOL_DEG, (
                f"A bowl sits {got - bare_mirror:+.3f} deg from the bare mirror of its dot; "
                f"DS_BACK_DIRECTION = +{BACK_DIRECTION} means {step_deg:+.3f} deg, toward the "
                "end of the line."
            )

    def test_four_tactile_arrows_one_per_row(self, ds_features, layout):
        """
        Consecutive arrows meet base-to-apex at the default 10 mm line spacing,
        so they are one connected band rather than four clusters. Count them by
        the row each belongs to instead, then pin the band's total extent so a
        fifth arrow, or a missing one, still fails.
        """
        np = ds_features.np
        seam = ds_features.raised & (np.abs(np.abs(ds_features.theta) - 180.0) < 10.0)
        assert seam.any(), "No raised material at the seam: the arrows are missing."

        half = layout["arrow_length"] / 2.0
        for row in range(layout["rows"]):
            y = _row_y(layout, row)
            here = seam & (np.abs(ds_features.z - y) < half - 0.5)
            assert here.any(), f"Row {row} (z={y:.1f} mm) has no raised arrow at the seam."
            assert (
                abs(ds_features.r[here].max() - (layout["radius"] + layout["arrow_raise"]))
                <= 0.01
            ), f"Row {row}'s arrow does not stand {layout['arrow_raise']} mm proud."

        top = _row_y(layout, 0) + half
        bottom = _row_y(layout, layout["rows"] - 1) - half
        z_seam = ds_features.z[seam]
        assert abs(z_seam.max() - top) <= Z_TOL_MM and abs(z_seam.min() - bottom) <= Z_TOL_MM, (
            f"The seam band spans z {z_seam.min():.3f}..{z_seam.max():.3f} mm; "
            f"{layout['rows']} arrows of {layout['arrow_length']} mm span {bottom:.3f}..{top:.3f} mm."
        )

    def test_no_visual_marker_columns(self, ds_features, layout):
        """
        Double-sided forces tactile, so the recessed triangle and square must be
        gone. If they were still cut, the recessed set would hold 8 more features
        at the first two column angles.
        """
        clusters = ds_features.clusters(ds_features.recessed)
        marker_angles = [
            math.degrees(layout["start_angle"]),
            math.degrees(layout["start_angle"] + layout["cell_angle"]),
        ]
        for cluster in clusters:
            for marker in marker_angles:
                assert abs(_ang_diff(cluster["theta"], marker)) > 1.0, (
                    f"A recess rendered at theta={cluster['theta']:.3f} deg, on a Visual "
                    "marker column. Double-sided must not draw the marker columns."
                )


class TestFootprints:
    """The Option B sizes reach the mesh, not just the constants block."""

    def test_bowl_cut_depth(self, ds_features, layout):
        """
        The number Phase 13 cross-validates against. The cut is a hemisphere of
        radius DS_BOWL_R, so it is DEEPER than DS_BOWL_DEPTH, by design - see
        this file's header. Tessellation takes a few micron off the pole.
        """
        sphere_r = (
            (layout["bowl_dia"] / 2) ** 2 + layout["bowl_depth"] ** 2
        ) / (2 * layout["bowl_depth"])
        depths = [
            layout["radius"] - c["r_min"] for c in ds_features.clusters(ds_features.recessed)
        ]
        measured = max(depths)
        print(
            f"\nMEASURED ds bowl cut depth = {measured:.4f} mm "
            f"(hemisphere of radius {sphere_r:.4f}; DS_BOWL_DEPTH is {layout['bowl_depth']})"
        )
        assert max(depths) - min(depths) <= 1e-6, f"Bowls cut to different depths: {depths}"
        assert abs(measured - MEASURED_BOWL_DEPTH_MM) <= BOWL_DEPTH_TOL_MM, (
            f"The bowl now cuts {measured:.4f} mm deep, not the {MEASURED_BOWL_DEPTH_MM} mm "
            "this file documents and Phase 13's cross-validation tolerances cite. Re-measure "
            "and update both, or find what moved."
        )
        assert measured > layout["bowl_depth"], (
            "The bowl cut no deeper than DS_BOWL_DEPTH, which means the sphere is no "
            "longer centred on the shell surface. That silently un-matches the web app, "
            "whose browser worker is the authoritative convention (decision 2026-08-19)."
        )
        assert measured < sphere_r, (
            "A tessellated hemisphere cannot cut deeper than its own radius."
        )

    def test_raised_dots_use_the_option_b_height(self, ds_features, layout):
        """
        Double-sided dots are 0.8 mm tall, not the 1.0 mm single-sided default.
        The dome is a tessellated spherical cap, so it lands just under nominal.
        """
        heights = [
            c["r_max"] - layout["radius"]
            for c in ds_features.clusters(ds_features.away_from_seam(ds_features.raised))
        ]
        for h in heights:
            assert 0.99 * layout["dot_height"] <= h <= layout["dot_height"], (
                f"A raised dot stands {h:.4f} mm proud; Option B is {layout['dot_height']} mm. "
                "Single-sided at the 0.4mm preset would be 1.0 mm."
            )


class TestForcedTactile:
    """Visual + double-sided renders tactile anyway, and says so."""

    @pytest.fixture(scope="class")
    def forced(self, ds_runner, _trimesh, layout, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("ds_forced_tactile")
        stl_path, output = _render(
            ds_runner, tmp_path, _ds_params(indicator_mode="Visual"), "forced"
        )
        return _Features(_trimesh, stl_path, layout), output

    def test_warning_is_echoed(self, forced):
        _, output = forced
        assert "WARNING:" in output and "indicator_mode" in output, (
            "double_sided On with indicator_mode Visual must echo a WARNING naming "
            f"indicator_mode.\noutput (truncated): {output[:800]}"
        )

    def test_arrows_are_rendered_anyway(self, forced, layout):
        features, _ = forced
        np = features.np
        seam = features.raised & (np.abs(np.abs(features.theta) - 180.0) < 0.5)
        assert seam.any(), "Forced tactile did not render the seam arrows."

    def test_marker_columns_are_still_dropped(self, forced, layout):
        features, _ = forced
        clusters = features.clusters(features.recessed)
        _match(clusters, _back_placements(layout, BACK_TEXT), "back bowls (forced tactile)")


class TestDoubleSidedOffIsInert:
    """With the gate Off the back text must not reach the geometry at all."""

    @pytest.mark.slow
    def test_back_text_changes_nothing_when_off(self, ds_runner, tmp_path):
        empty, _ = _render(
            ds_runner,
            tmp_path,
            {"indicator_mode": "Tactile", "Line_1": FRONT_TEXT, "Line_2": ""},
            "off_no_back",
        )
        filled, _ = _render(
            ds_runner,
            tmp_path,
            {
                "indicator_mode": "Tactile",
                "Line_1": FRONT_TEXT,
                "Line_2": "",
                "Back_Line_1": BACK_TEXT,
            },
            "off_with_back",
        )
        assert empty.read_bytes() == filled.read_bytes(), (
            "Filling Back_Line_1 changed the STL with double_sided Off. Toggling the "
            "feature off must be byte-identical to single-sided."
        )


class TestSourceGuards:
    """Text-only checks, so they still run in the no-OpenSCAD CI job."""

    def test_back_line_fields_are_declared(self, scad_source):
        missing = [
            f"Back_Line_{n}"
            for n in range(1, 11)
            if not re.search(rf'^Back_Line_{n}\s*=\s*""', scad_source, re.MULTILINE)
        ]
        assert not missing, (
            f"Missing Back_Line_N declarations: {missing}. There must be one per row "
            "the grid_rows slider allows, exactly as for Line_N."
        )

    def test_all_back_lines_is_the_single_source_of_truth(self, scad_source):
        match = re.search(r"_all_back_lines\s*=\s*\[([^\]]+)\]", scad_source)
        assert match, "_all_back_lines assignment not found"
        listed = [item.strip() for item in match.group(1).replace("\n", " ").split(",")]
        assert listed == [f"Back_Line_{n}" for n in range(1, 11)], (
            f"_all_back_lines must be exactly Back_Line_1..Back_Line_10 in row order, got: {listed}"
        )

    def test_no_back_line_n_referenced_outside_its_declaration(self, scad_source):
        code = re.sub(r"_all_back_lines\s*=\s*\[[^\]]+\]", "", scad_source)
        code = re.sub(r'^Back_Line_\d+\s*=\s*"[^"]*";.*$', "", code, flags=re.MULTILINE)
        code = re.sub(r"^\s*//.*$", "", code, flags=re.MULTILINE)
        stray = sorted(set(re.findall(r"\bBack_Line_\d+\b", code)))
        assert not stray, (
            f"Back_Line_N referenced outside its declaration and _all_back_lines: {stray}. "
            "Iterate _all_back_lines instead."
        )

    def test_double_sided_forces_tactile(self, scad_source):
        assert re.search(
            r'tactile_on\s*=\s*\(indicator_mode\s*==\s*"Tactile"\)\s*\|\|\s*ds_on\s*;',
            scad_source,
        ), (
            "tactile_on must be forced true by ds_on. Everything downstream - the grid "
            "columns, the seam gap, the marker columns, the arrows - reads it."
        )
        assert re.search(
            r'ds_forced_tactile\s*=\s*ds_on\s*&&\s*\(indicator_mode\s*!=\s*"Tactile"\)\s*;',
            scad_source,
        )

    def test_forced_tactile_echoes_a_console_warning(self, scad_source):
        block = scad_source[scad_source.index("if (ds_forced_tactile)") :][:600]
        assert "echo(" in block and "WARNING:" in block, (
            "The forced-tactile override must echo a WARNING line for desktop users; "
            "the 3D text alone only reaches the MakerWorld preview."
        )

    def test_signed_off_direction_and_footprint(self, scad_source):
        """
        The two D2/D3 numbers this file's expected positions are built on. Pinned
        here so a change to either shows up as a decision to re-confirm with
        Brennen, not as a silently self-consistent test suite.
        """
        assert _scad_constant("DS_BACK_DIRECTION") == BACK_DIRECTION, (
            "DS_BACK_DIRECTION changed. It decides which side of the seam arrow the "
            "back features crowd, was confirmed on a printed pair, and no clearance "
            "number can catch a wrong choice - both signs measure the same distances."
        )
        assert (
            _scad_constant("DS_DOT_BASE_H") + _scad_constant("DS_DOT_DOME_H")
            == OPTION_B_DOT_HEIGHT_MM
        ), "The Option B raised dot height changed; that is a tactile-readability decision."

    def test_back_grid_transform_matches_interpoint_py(self, scad_source):
        """
        back_grid_transform(x, z) = (-x + direction * offset_x, z + direction * offset_z).
        Written in angles here, so the circumferential term is divided by the radius.
        """
        assert re.search(
            r"back_angle_rad\s*=\s*-front_angle_rad\s*\+\s*DS_BACK_DIRECTION\s*\*\s*"
            r"\(interpoint_offset_x_mm\s*/\s*radius\)",
            scad_source,
        ), (
            "The back angle must be the NEGATED front angle (the mirror about the seam "
            "plane) plus DS_BACK_DIRECTION * offset_x as an angle."
        )
        assert re.search(
            r"back_dot_y\s*=\s*front_dot_y\s*\+\s*DS_BACK_DIRECTION\s*\*\s*interpoint_offset_y_mm",
            scad_source,
        ), "The back height must be the front height plus DS_BACK_DIRECTION * offset_y."

    def test_recesses_are_subtracted_after_the_raised_dots_are_unioned(self, scad_source):
        """
        Shell -> union raised -> subtract recesses, the same order the web app's
        manifold worker uses. Reversing it buries a bowl under a neighbouring dot.
        """
        body = scad_source[scad_source.index("module cylinder_emboss_plate()") :]
        body = body[: body.index("module cylinder_counter_plate()")]
        assert body.index("braille_dot_for_plate()") < body.index("ds_back_recesses()"), (
            "ds_back_recesses() must come after the raised dots in cylinder_emboss_plate()."
        )
        assert "if (ds_on) {\n                ds_back_recesses();" in body, (
            "ds_back_recesses() must be gated on ds_on and sit inside the difference()."
        )

    def test_option_b_footprints_drive_the_geometry(self, scad_source):
        """
        The ds dot and bowl must be built from the DS_* constants, so the signed-off
        footprints cannot be edited in one place and missed in another.
        """
        for module, names in (
            (
                "module ds_braille_dot_centered()",
                ["DS_DOT_BASE_H", "DS_DOT_BASE_DIA", "DS_DOT_DOME_DIA", "DS_DOT_DOME_R", "DS_DOT_HEIGHT"],
            ),
            ("module ds_counter_recess()", ["DS_BOWL_R"]),
        ):
            start = scad_source.index(module)
            block = scad_source[start : start + 1200]
            block = block[: block.index("\n}\n") + 3]
            for name in names:
                assert name in block, f"{module} must be built from {name}, not a literal."

    def test_ds_dot_overrides_the_shape_selection_and_the_preset(self, scad_source):
        assert re.search(
            r"active_emboss_height\s*=\s*ds_on\s*\?\s*DS_DOT_HEIGHT\s*:", scad_source
        ), (
            "active_emboss_height must take the ds branch FIRST, so neither the "
            "Rounded/Cone dropdown nor a paper-thickness preset can reach the "
            "double-sided footprint."
        )
        assert re.search(
            r"module\s+braille_dot_for_plate\(\)\s*\{\s*if\s*\(ds_on\)\s*\{\s*ds_braille_dot_centered\(\);",
            scad_source,
        )

    def test_bowl_is_a_hemisphere_centred_on_the_surface(self, scad_source):
        """
        R = (a^2 + h^2) / (2h), and the sphere sits AT the module origin, which
        the callers put on the shell surface. That is the web app's browser-worker
        convention, authoritative by decision 2026-08-19, and it makes the printed
        bowl a hemisphere R deep and 2R across rather than DS_BOWL_DEPTH deep.
        """
        assert re.search(
            r"DS_BOWL_R\s*=\s*\(\(DS_BOWL_DIA\s*/\s*2\)\s*\*\s*\(DS_BOWL_DIA\s*/\s*2\)\s*"
            r"\+\s*DS_BOWL_DEPTH\s*\*\s*DS_BOWL_DEPTH\)\s*/\s*\(2\s*\*\s*DS_BOWL_DEPTH\)",
            scad_source,
        )
        start = scad_source.index("module ds_counter_recess()")
        body = scad_source[start : scad_source.index("\n}\n", start)]
        assert "translate" not in body, (
            "ds_counter_recess() must place the sphere at its own origin, with no radial "
            "translate. Offsetting it outward reverts to the nominal-depth convention and "
            "silently un-matches the web app, which is what actually gets printed."
        )
        assert re.search(r"sphere\s*\(\s*r\s*=\s*DS_BOWL_R", body)

    def test_warning_strings_are_present(self, scad_source):
        """
        DRAFT wording, pending sign-off. If these strings change, the change was
        reviewed - update this guard in the same edit.
        """
        assert '"DOUBLE-SIDED REQUIRES TACTILE"' in scad_source
        assert '"DOTS TOO CLOSE: "' in scad_source

    def test_crowding_warning_uses_the_constants_not_literals(self, scad_source):
        assert re.search(
            r"ds_same_surface_gap\s*=\s*ds_on\s*\?\s*ds_same_surface_min_gap\("
            r"DS_DOT_BASE_DIA,\s*DS_BOWL_DIA,",
            scad_source,
        ), (
            "The crowding warning must measure the footprints the geometry actually "
            "uses, so editing Option B moves the warning with it."
        )
        assert re.search(
            r"ds_dots_too_close\s*=\s*ds_on\s*&&\s*\(ds_same_surface_gap\s*<\s*DS_GAP_RELIABLE\)",
            scad_source,
        )
