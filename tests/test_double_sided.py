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
3. The fixed footprints, keyed to ``paper_thickness_preset`` since 2026-08-20
   (FD-8/FD-9): the "0.3mm" preset renders Option B (dot 1.2 mm base x 0.8 mm
   tall, bowl 1.3 x 0.5), everything else renders Q2, the print-matrix winner
   (dot 1.2 x 1.0 mm tall with a 1.0 mm dome, bowl 1.4 x 0.5) - because a
   raised dot and a recess share one surface, and one footprint cannot serve
   both card stocks.

Two kinds of test live here, following ``tests/test_interpoint_math_scad.py``:

* **Render tests** run OpenSCAD, load the STL with trimesh and probe it. The
  reference model is front ``a b c`` (5 raised dots) and back ``d e f`` (8
  bowls) on the shipped defaults, which is small enough to render in about a
  second. They skip when no OpenSCAD binary is available.
* **Source guards** read the .scad as text and run everywhere, including the
  no-OpenSCAD CI job.

MEASURED, 2026-08-19/20, OpenSCAD 2026.01.03 Manifold: this repo cuts the 0.3
package's 1.3 mm bowl **0.6693 mm** deep and the 0.4 package's 1.4 mm bowl
**0.7364 mm** deep below the nominal cylinder radius. Neither is the 0.5 mm
``DS_BOWL_DEPTH`` suggests, and neither is meant to be: the bowl's sphere is
centred ON the shell surface, so the cut is a hemisphere of radius ``DS_BOWL_R``
(0.6725 / 0.7400 mm), and the few-micron shortfall is sphere tessellation (at
``quality_fn`` = 32 the deepest ring sits at 84.375 deg of latitude:
0.6725 * sin(84.375) = 0.66926; 0.7400 * sin(84.375) = 0.73644).

That convention is deliberate, decided 2026-08-19: it matches
``static/workers/csg-worker-manifold.js`` in the web repo, which is the geometry
that has actually been printed and embossed. The web app's own Python renderer,
and this file's SINGLE-SIDED counter plate, both use the other convention -
centre (R - depth) outside the surface, cut exactly the nominal depth - and are
deliberately left alone. Phase 13's cross-validation tolerances cite these two
numbers (0.6693 / 0.7364 mm).

License: PolyForm Noncommercial 1.0.0
"""

import json
import math
import os
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
PRESETS_FILE = PROJECT_ROOT / "presets.scad"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import (  # noqa: E402  (shared helpers)
    BRAILLE_FULL_CELL,
    _resolve_openscad_path,
    _scad_constant,
    _z_max,
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

# The signed-off footprint packages, hardcoded on purpose for the same reason
# (FD-8/FD-9, 2026-08-20): paper_thickness_preset "0.3mm" renders Option B,
# validated on 0.3 mm stock 2026-08-17; every other value - "0.4mm" is the
# shipped default - renders Q2, validated on 0.4 mm stock 2026-08-20.
#   dot_height     base + dome, mm
#   bowl_dia       nominal bowl opening, mm (a shape input, not the mouth)
#   measured_bowl  the tessellated hemisphere cut depth, mm - the number this
#                  file's docstring quotes and Phase 13's tolerances cite
PACKAGES = {
    "0.4mm": dict(dot_height=1.0, bowl_dia=1.4, measured_bowl=0.7364),
    "0.3mm": dict(dot_height=0.8, bowl_dia=1.3, measured_bowl=0.6693),
}
DEFAULT_PACKAGE = "0.4mm"  # paper_thickness_preset's shipped default

# How close a rendered feature must land to where the maths puts it.
ANGLE_TOL_DEG = 0.05
Z_TOL_MM = 0.01
# How far a measured bowl depth may drift before the numbers quoted above stop
# being true.
BOWL_DEPTH_TOL_MM = 0.002


def _preset_value(key, table="PRESET_04"):
    """Pull a numeric value out of a paper-thickness preset table."""
    text = PRESETS_FILE.read_text(encoding="utf-8")
    block = text[text.index(f"{table} = [") :]
    block = block[: block.index("];")]
    m = re.search(rf'\["{re.escape(key)}",\s*([0-9.+\-]+)\]', block)
    assert m, f"`{key}` is not in the {table} table"
    return float(m.group(1))


@pytest.fixture(scope="module")
def scad_source():
    return SCAD_FILE.read_text(encoding="utf-8")


def _layout_from(radius, cols, rows, package, height=None, table="PRESET_04"):
    """
    A cylinder layout, re-derived from the preset table and the sliders rather
    than copied out of the geometry code under test.

    Phase 13 calls this with the golden pair's grid and radius as well as the
    shipped defaults, so both configurations are built by one set of formulas.
    """
    height = _preset_value("cylinder_height_mm", table=table) if height is None else height
    cell = _preset_value("cell_spacing", table=table)
    line = _preset_value("line_spacing", table=table)
    dot = _preset_value("dot_spacing", table=table)

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
        "bowl_dia": PACKAGES[package]["bowl_dia"],
        "bowl_depth": _scad_constant("DS_BOWL_DEPTH"),
        "dot_height": PACKAGES[package]["dot_height"],
        "arrow_raise": _scad_constant("tactile_indicator_raise"),
        "arrow_length": _scad_constant("tactile_indicator_length"),
        "arrow_extra_depth": _scad_constant("tactile_recess_extra_depth"),
    }


@pytest.fixture(scope="module")
def layout():
    """The shipped-default cylinder layout."""
    return _layout_from(
        radius=_preset_value("cylinder_diameter_mm") / 2,
        cols=_scad_constant("grid_columns"),
        rows=_scad_constant("grid_rows"),
        package=DEFAULT_PACKAGE,
    )


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


def _negated(placements):
    """The counter plate's angle-negation mirror, applied to planar placements."""
    return [(-angle, y) for angle, y in placements]


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
    """The active package's sizes reach the mesh, not just the constants block."""

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
        expected_bowl = PACKAGES[DEFAULT_PACKAGE]["measured_bowl"]
        assert abs(measured - expected_bowl) <= BOWL_DEPTH_TOL_MM, (
            f"The bowl now cuts {measured:.4f} mm deep, not the {expected_bowl} mm "
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

    def test_raised_dots_use_the_active_package_height(self, ds_features, layout):
        """
        The default preset renders the Q2 package: 1.0 mm tall - the same height
        as the single-sided 0.4 die but on a 1.2 mm base, not 1.5. The dome is a
        tessellated spherical cap, so it lands just under nominal.
        """
        heights = [
            c["r_max"] - layout["radius"]
            for c in ds_features.clusters(ds_features.away_from_seam(ds_features.raised))
        ]
        for h in heights:
            assert 0.99 * layout["dot_height"] <= h <= layout["dot_height"], (
                f"A raised dot stands {h:.4f} mm proud; the active package is "
                f"{layout['dot_height']} mm."
            )


class TestPackage03Geometry:
    """paper_thickness_preset \"0.3mm\" renders the Option B package."""

    @pytest.fixture(scope="class")
    def features_03(self, ds_runner, _trimesh, layout, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("ds_package_03")
        stl_path, output = _render(
            ds_runner,
            tmp_path,
            _ds_params(paper_thickness_preset="0.3mm"),
            "package_03",
        )
        assert "ERROR:" not in output, f"Render reported an error:\n{output[:800]}"
        return _Features(_trimesh, stl_path, layout)

    def test_dot_height_is_option_b(self, features_03, layout):
        pkg = PACKAGES["0.3mm"]
        heights = [
            c["r_max"] - layout["radius"]
            for c in features_03.clusters(features_03.away_from_seam(features_03.raised))
        ]
        assert heights, "No raised dots found on the 0.3-package render."
        for h in heights:
            assert 0.99 * pkg["dot_height"] <= h <= pkg["dot_height"], (
                f"A raised dot stands {h:.4f} mm proud; the 0.3 package (Option B) "
                f"is {pkg['dot_height']} mm."
            )

    def test_bowl_cut_depth_is_option_b(self, features_03, layout):
        pkg = PACKAGES["0.3mm"]
        depths = [
            layout["radius"] - c["r_min"]
            for c in features_03.clusters(features_03.recessed)
        ]
        assert depths, "No bowls found on the 0.3-package render."
        measured = max(depths)
        assert abs(measured - pkg["measured_bowl"]) <= BOWL_DEPTH_TOL_MM, (
            f"The 0.3-package bowl cuts {measured:.4f} mm deep, not the "
            f"{pkg['measured_bowl']} mm this file documents."
        )

    def test_positions_are_unchanged_by_the_package(self, features_03, layout):
        """Both preset tables share the same spacing, so only sizes may move."""
        clusters = features_03.clusters(features_03.recessed)
        _match(clusters, _back_placements(layout, BACK_TEXT), "back bowls (0.3 package)")


@pytest.fixture(scope="module")
def ds_b_features(ds_runner, _trimesh, layout, tmp_path_factory):
    """Cylinder B - the counter plate - on the same reference model."""
    tmp_path = tmp_path_factory.mktemp("double_sided_b")
    stl_path, output = _render(
        ds_runner, tmp_path, _ds_params(plate_type="negative"), "cylinder_b"
    )
    assert "ERROR:" not in output, f"Render reported an error:\n{output[:800]}"
    return _Features(_trimesh, stl_path, layout)


class TestCylinderBGeometry:
    """
    The counter plate in double-sided mode: 8 raised back-text dots, 5 front
    bowls (one per ACTUAL front dot - the universal grid is gone), 4 recessed
    seam arrows. Every feature sits at exactly minus its Cylinder A partner's
    angle with the same height, because this plate is A's angle-negation
    mirror.
    """

    def test_raised_back_dots_at_the_negated_back_grid(self, ds_b_features, layout):
        clusters = ds_b_features.clusters(
            ds_b_features.away_from_seam(ds_b_features.raised)
        )
        pairs = _match(
            clusters, _negated(_back_placements(layout, BACK_TEXT)), "B raised back dots"
        )
        assert len(pairs) == EXPECTED_BACK_BOWLS

    def test_back_dots_use_the_active_package_height(self, ds_b_features, layout):
        heights = [
            c["r_max"] - layout["radius"]
            for c in ds_b_features.clusters(
                ds_b_features.away_from_seam(ds_b_features.raised)
            )
        ]
        assert heights, "No raised back dots found on Cylinder B."
        for h in heights:
            assert 0.99 * layout["dot_height"] <= h <= layout["dot_height"], (
                f"A raised back dot stands {h:.4f} mm proud; the active package "
                f"is {layout['dot_height']} mm."
            )

    def test_front_bowls_are_one_per_actual_front_dot(self, ds_b_features, layout):
        """
        1:1 with the FRONT text, at the mirrored positions - and only 5 of
        them, which is also the proof the universal grid is gone: a universal
        field would put a recess at all 6 positions of all 13 cells of all 4
        rows.
        """
        clusters = ds_b_features.clusters(
            ds_b_features.away_from_seam(ds_b_features.recessed)
        )
        pairs = _match(
            clusters, _negated(_front_placements(layout, FRONT_TEXT)), "B front bowls"
        )
        assert len(pairs) == EXPECTED_FRONT_DOTS

    def test_front_bowl_cut_depth_matches_cylinder_a(self, ds_b_features, layout):
        """Both plates call the same ds_counter_recess(), so the same measured
        hemisphere cut - the number Phase 13's tolerances cite."""
        depths = [
            layout["radius"] - c["r_min"]
            for c in ds_b_features.clusters(
                ds_b_features.away_from_seam(ds_b_features.recessed)
            )
        ]
        assert depths, "No front bowls found on Cylinder B."
        measured = max(depths)
        expected_bowl = PACKAGES[DEFAULT_PACKAGE]["measured_bowl"]
        assert abs(measured - expected_bowl) <= BOWL_DEPTH_TOL_MM, (
            f"Cylinder B's bowls cut {measured:.4f} mm deep, not the "
            f"{expected_bowl} mm this file documents for the active package."
        )

    def test_recessed_arrows_one_per_row(self, ds_b_features, layout):
        """
        The tactile arrows are RECESSED on this plate, one per row, cut
        raise + extra depth below the surface (the floor is a 64-gon band, so
        CSG vertices may sit up to the face sagitta deeper than nominal).
        """
        np = ds_b_features.np
        seam = ds_b_features.recessed & (
            np.abs(np.abs(ds_b_features.theta) - 180.0) < 10.0
        )
        assert seam.any(), "No recessed material at the seam: the arrow recesses are missing."

        half = layout["arrow_length"] / 2.0
        for row in range(layout["rows"]):
            y = _row_y(layout, row)
            here = seam & (np.abs(ds_b_features.z - y) < half - 0.5)
            assert here.any(), f"Row {row} (z={y:.1f} mm) has no arrow recess at the seam."

        depth = layout["radius"] - ds_b_features.r[seam].min()
        nominal = layout["arrow_raise"] + layout["arrow_extra_depth"]
        assert nominal - 0.01 <= depth <= nominal + 0.02, (
            f"The arrow recess cuts {depth:.3f} mm below the surface; nominal "
            f"is {nominal} mm (raise + extra depth)."
        )


_DS_PAIR_RE = re.compile(
    r"DS_PAIR (A|B) (front_dot|back_recess|front_bowl|back_dot) "
    r"deg=(-?\d+\.\d{6}) y=(-?\d+\.\d{6})"
)


@pytest.fixture(scope="module")
def pairing_echoes(ds_runner, tmp_path_factory):
    """DS_PAIR rows echoed by both plates' actual placement code."""
    tmp_path = tmp_path_factory.mktemp("ds_pairing")
    _, out_a = _render(ds_runner, tmp_path, _ds_params(ds_self_check=True), "pair_a")
    _, out_b = _render(
        ds_runner,
        tmp_path,
        _ds_params(ds_self_check=True, plate_type="negative"),
        "pair_b",
    )

    def rows_of(output, plate):
        rows = {}
        for match in _DS_PAIR_RE.finditer(output):
            assert match.group(1) == plate, (
                f"A DS_PAIR row for plate {match.group(1)} appeared in the "
                f"plate-{plate} render: {match.group(0)}"
            )
            rows.setdefault(match.group(2), []).append((match.group(3), match.group(4)))
        return rows

    return rows_of(out_a, "A"), rows_of(out_b, "B")


class TestPairingCrossCheck:
    """
    The heart of the phase: every Cylinder A feature and its Cylinder B partner
    sit at EXACT angle negation with the same height. The rows come from the
    placement code itself (ds_fmt_e6 rounds to 1e-6 and prints all six
    decimals), and both plates walk the text in the same order, so partners are
    compared row for row and string for string - a drifted walk echoes a
    different row, with no mesh tolerance to hide behind.
    """

    @staticmethod
    def _assert_partners(a_rows, b_rows, label):
        assert len(a_rows) == len(b_rows), (
            f"{label}: A placed {len(a_rows)} features, B placed {len(b_rows)} - "
            "the two plates disagree about the text."
        )
        for (deg_a, y_a), (deg_b, y_b) in zip(a_rows, b_rows):
            assert y_a == y_b, f"{label}: partner heights differ, {y_a} vs {y_b} mm."
            assert deg_a.lstrip("-") == deg_b.lstrip("-"), (
                f"{label}: partner angles are not the same magnitude after the "
                f"same 1e-6 rounding, {deg_a} vs {deg_b} deg."
            )
            assert abs(float(deg_a) + float(deg_b)) <= 1e-6, (
                f"{label}: partner angles are not negations, {deg_a} vs {deg_b} deg."
            )

    def test_every_front_dot_has_a_bowl_partner(self, pairing_echoes):
        a, b = pairing_echoes
        assert len(a.get("front_dot", [])) == EXPECTED_FRONT_DOTS, (
            "Cylinder A did not echo one DS_PAIR row per front dot."
        )
        self._assert_partners(
            a["front_dot"], b.get("front_bowl", []), "front dot vs front bowl"
        )

    def test_every_back_recess_has_a_raised_dot_partner(self, pairing_echoes):
        a, b = pairing_echoes
        assert len(a.get("back_recess", [])) == EXPECTED_BACK_BOWLS, (
            "Cylinder A did not echo one DS_PAIR row per back recess."
        )
        self._assert_partners(
            a["back_recess"], b.get("back_dot", []), "back recess vs back dot"
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
        for name, pkg_03, pkg_04 in (
            ("DS_DOT_BASE_H", 0.4, 0.5),
            ("DS_DOT_DOME_H", 0.4, 0.5),
        ):
            match = re.search(
                rf"^{name}\s*=\s*ds_use_03_package\s*\?\s*([\d.]+)\s*:\s*([\d.]+)\s*;",
                scad_source,
                re.MULTILINE,
            )
            assert match, f"{name} must be keyed on ds_use_03_package"
            assert (float(match.group(1)), float(match.group(2))) == (pkg_03, pkg_04), (
                f"{name} changed; the package dot heights (0.8 / 1.0 mm) are "
                "tactile-readability decisions signed off 2026-08-16 / 2026-08-20."
            )

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
        SIGNED OFF by Brennen 2026-08-20, as one batch of eight (the five here
        plus the two tactile wall-guard strings in test_tactile_mode.py and the
        printability guard message in test_interpoint_math_scad.py). Reword only
        with his sign-off, and update this guard in the same edit.
        """
        assert '"DOUBLE-SIDED REQUIRES TACTILE"' in scad_source
        assert '"DOTS TOO CLOSE: "' in scad_source
        assert '"WARNING: Back_Line_"' in scad_source
        assert '"WARNING: back text reaches Back_Line_"' in scad_source
        assert '"Double-sided: this render is Cylinder "' in scad_source

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
            r"ds_dots_too_close\s*=\s*ds_on\s*&&\s*\(ds_same_surface_gap\s*<\s*DS_GAP_ACCEPTED\)",
            scad_source,
        )
        assert re.search(
            r"DS_GAP_ACCEPTED\s*=\s*ds_use_03_package\s*\?\s*DS_GAP_RELIABLE\s*:\s*DS_GAP_FLOOR\s*;",
            scad_source,
        ), (
            "The physical DOTS TOO CLOSE warning must accept the 0.4 package's "
            "designed 0.468 mm gap (printed ridge measured clean 2026-08-20) and "
            "fire only below the floor there; the 0.3 package keeps the reliable "
            "line. RATIFIED by Brennen 2026-08-20, alongside the decision that "
            "only the hard assert moved onto the printed ridge."
        )

    def test_universal_grid_is_gated_off_in_ds_mode(self, scad_source):
        """
        In double-sided mode every recess is the 1:1 partner of an actual dot;
        the "recesses for ALL possible dot positions" loop runs only when NOT
        ds_on, exactly as the web generator's Cylinder B branch skips it.
        """
        body = scad_source[scad_source.index("module cylinder_counter_plate()") :]
        assert "if (!ds_on)" in body, (
            "The counter plate's universal recess grid must be gated on !ds_on."
        )
        assert body.index("if (!ds_on)") < body.index("counter_last_col"), (
            "The !ds_on gate must wrap the universal grid loop, not follow it."
        )
        assert re.search(r"if \(ds_on\) \{\s*ds_front_recesses\(\);", body), (
            "cylinder_counter_plate() must subtract ds_front_recesses() - the 1:1 "
            "bowls for Cylinder A's actual front dots - when ds_on."
        )

    def test_counter_back_dots_are_unioned_before_the_bowls_are_subtracted(
        self, scad_source
    ):
        """
        Shell -> union raised -> subtract recesses on this plate too, the web
        manifold worker's order. Reversing it buries a bowl under a
        neighbouring raised back dot.
        """
        body = scad_source[scad_source.index("module cylinder_counter_plate()") :]
        assert re.search(r"if \(ds_on\) \{\s*ds_back_raised_dots\(\);", body), (
            "cylinder_counter_plate() must union ds_back_raised_dots() when ds_on."
        )
        assert body.index("cylinder_shell") < body.index("ds_back_raised_dots()") < body.index(
            "ds_front_recesses()"
        ), (
            "The raised back dots must be unioned with the shell before the "
            "front bowls are subtracted."
        )

    def test_both_plates_share_the_back_walk(self, scad_source):
        """
        One placement module drives BOTH plates' back grids - the emboss bowls
        at angle_sign +1 and the counter plate's raised dots at -1 - so the two
        walks cannot drift apart. That shared walk is what makes the pairing
        cross-check exact rather than merely close.
        """
        assert re.search(
            r'module ds_back_recesses\(\)\s*\{\s*'
            r'ds_back_placements\(1,\s*0,\s*"A back_recess"\)\s*ds_counter_recess\(\);',
            scad_source,
        ), "ds_back_recesses() must be a thin wrapper over ds_back_placements()."
        assert re.search(
            r'module ds_back_raised_dots\(\)\s*\{\s*'
            r'ds_back_placements\(-1,\s*DS_DOT_HEIGHT\s*/\s*2,\s*"B back_dot"\)\s*'
            r'ds_braille_dot_centered\(\);',
            scad_source,
        ), "ds_back_raised_dots() must be a thin wrapper over ds_back_placements()."


# ---------------------------------------------------------------------------
# Phase 12: the Customizer surface, and the back-line validation it carries
# ---------------------------------------------------------------------------

DS_TAB = "/* [Double-Sided Card (BETA)] */"
# tests/validate_parameter_schema.py stops parsing at the FIRST /* [Hidden] */,
# and the Customizer hides everything grouped under one, so a control declared
# below it reaches neither.
FIRST_HIDDEN = "/* [Hidden] */"
SYNC_MARKER = "// BACKWARD COMPATIBILITY - Test System Parameters"


def _ds_tab_body(scad_source):
    """Everything between the double-sided tab header and the next tab header."""
    start = scad_source.index(DS_TAB)
    return scad_source[start : scad_source.index("/* [", start + len(DS_TAB))]


class TestCustomizerSurface:
    """
    The double-sided controls became user-facing in Phase 12. Text-only, so they
    run in the no-OpenSCAD CI job.
    """

    def test_the_tab_exists_and_sits_above_both_markers(self, scad_source):
        assert DS_TAB in scad_source, "The [Double-Sided Card (BETA)] tab is missing."
        assert scad_source.index(DS_TAB) < scad_source.index(FIRST_HIDDEN), (
            "The tab must sit above the first /* [Hidden] */ or neither the "
            "Customizer nor the parameter-schema validator will see its controls."
        )
        assert scad_source.index(DS_TAB) < scad_source.index(SYNC_MARKER), (
            "Everything from the MakerWorld sync marker to EOF is re-flattened in "
            "its own phase, so parameters must stay above it."
        )

    def test_the_tab_holds_every_double_sided_control(self, scad_source):
        body = _ds_tab_body(scad_source)
        assert 'double_sided = "Off"; // [Off, On]' in body, (
            "The gate must be a dropdown in this tab, defaulting to Off so "
            "toggle-off behaviour stays the single-sided behaviour."
        )
        missing = [
            f"Back_Line_{n}"
            for n in range(1, 11)
            if not re.search(rf'^Back_Line_{n}\s*=\s*""', body, re.MULTILINE)
        ]
        assert not missing, (
            f"Back_Line fields outside the double-sided tab: {missing}. All ten "
            "rows live here - the front's 8 + 2 split exists only to cap the "
            "always-visible main text tab at eight fields."
        )
        for axis in ("x", "y"):
            assert f"interpoint_offset_{axis}_mm = 1.25; // [1.15:0.01:1.35]" in body

    def test_the_offset_sliders_match_the_range_the_guard_enforces(self, scad_source):
        """
        A slider wider than the assert lets a user pick a value that refuses to
        render; a narrower one hides legal values. They must be the same numbers.
        """
        low = _scad_constant("DS_OFFSET_MIN_MM")
        high = _scad_constant("DS_OFFSET_MAX_MM")
        for axis in ("x", "y"):
            match = re.search(
                rf"^interpoint_offset_{axis}_mm\s*=\s*[\d.]+\s*;\s*//\s*"
                r"\[([\d.]+):[\d.]+:([\d.]+)\]",
                scad_source,
                re.MULTILINE,
            )
            assert match, f"interpoint_offset_{axis}_mm is not declared as a slider"
            assert (float(match.group(1)), float(match.group(2))) == (low, high), (
                f"interpoint_offset_{axis}_mm slider is "
                f"[{match.group(1)}, {match.group(2)}] but the render guard "
                f"enforces [{low}, {high}]."
            )

    def test_ds_self_check_stays_hidden(self, scad_source):
        """A test hook, not a user control."""
        assert scad_source.index(FIRST_HIDDEN) < scad_source.index("ds_self_check ="), (
            "ds_self_check must stay under a /* [Hidden] */ group; exposing it "
            "would put a debug echo switch in front of users."
        )

    def test_the_footprints_are_not_exposed_as_dials(self, scad_source):
        """
        FD-8/FD-9: the ds dot and bowl ship fixed and keyed to
        paper_thickness_preset. Tactile geometry is the accessibility feature -
        it must not become something a user can nudge from the Customizer.
        """
        body = _ds_tab_body(scad_source)
        exposed = [
            name
            for name in (
                "DS_DOT_BASE_DIA",
                "DS_DOT_BASE_H",
                "DS_DOT_DOME_DIA",
                "DS_DOT_DOME_H",
                "DS_BOWL_DIA",
                "DS_BOWL_DEPTH",
            )
            if name in body
        ]
        assert not exposed, f"Double-sided footprints exposed in the Customizer: {exposed}"


class TestBackLineValidationSource:
    """
    Phase 10 wired the back text into the geometry but deliberately left the
    warnings out, so English pasted into a Back_Line produced a silently blank
    back side and nothing said why. These pin the fix.
    """

    def test_invalid_characters_covers_the_back_lines_on_both_plates(self, scad_source):
        start = scad_source.index("module invalid_characters_warning()")
        body = scad_source[start : scad_source.index("\n}\n", start)]
        assert "_all_lines" in body and "_all_back_lines" in body, (
            "The INVALID CHARACTERS check must read both faces' line lists."
        )
        assert "ds_on" in body, (
            "The back half of the check must be gated on the double-sided gate, "
            "so back text that is never read is never complained about."
        )
        assert scad_source.count("invalid_characters_warning();") == 2, (
            "Both plates must render it. In double-sided mode the BACK text is "
            "what the COUNTER plate raises, so a bad Back_Line blanks that plate."
        )

    def test_cell_capacity_counts_the_back_lines(self, scad_source):
        assert (
            "_back_max_line_len  = ds_on ? max([for (l = _all_back_lines) len(l)]) : 0;"
            in scad_source
        ), "The cell-capacity check must measure the back lines while ds_on."
        assert (
            "max_line_len = max(_front_max_line_len, _back_max_line_len);" in scad_source
        ), "TEXT TOO LONG must fire on the widest row of EITHER face."

    def test_row_capacity_counts_the_back_lines(self, scad_source):
        assert "rows_used = max(_front_rows_used, _back_rows_used);" in scad_source, (
            "TOO MANY LINES must fire on the deepest filled row of EITHER face."
        )
        assert "too_many_rows = rows_used > active_grid_rows" in scad_source
        assert "_filled_back_row_idx = ds_on" in scad_source, (
            "The back row scan must be gated on the double-sided gate."
        )


class TestBackLineWarningsRender:
    """The warnings actually fire - and only while the gate is On."""

    @pytest.fixture(scope="class")
    def baseline_z(self, ds_runner, _trimesh, tmp_path_factory):
        """Z-max of the reference double-sided model, which warns about nothing."""
        tmp_path = tmp_path_factory.mktemp("ds_warn_baseline")
        stl_path, output = _render(ds_runner, tmp_path, _ds_params(), "ds_baseline")
        assert "WARNING:" not in output, (
            "The reference double-sided model must render clean - scad-check.ps1 "
            f"greps for exactly that token.\noutput (truncated): {output[:800]}"
        )
        return _z_max(_trimesh, stl_path)

    def test_english_in_a_back_line_warns_in_3d(
        self, ds_runner, _trimesh, tmp_path, baseline_z
    ):
        """
        get_dot_pattern() returns an all-zero pattern for non-braille, so
        untranslated back text renders no bowls at all. Without the warning the
        export looks finished and the back of the card comes out empty.
        """
        stl_path, _ = _render(
            ds_runner, tmp_path, _ds_params(Back_Line_1="hello"), "ds_back_invalid"
        )
        depth = _scad_constant("INVALID_TEXT_DEPTH")
        z_max = _z_max(_trimesh, stl_path)
        assert z_max >= baseline_z + depth, (
            f"English in Back_Line_1 did not raise the bounding box by "
            f"INVALID_TEXT_DEPTH ({depth} mm): baseline={baseline_z:.3f}, "
            f"invalid={z_max:.3f}. The INVALID CHARACTERS warning did not fire, "
            "which is the silently blank back side this check exists to prevent."
        )

    def test_the_gate_keeps_the_back_check_quiet(
        self, ds_runner, _trimesh, tmp_path, baseline_z
    ):
        """Off must not complain about back text it never reads."""
        stl_path, _ = _render(
            ds_runner,
            tmp_path,
            _ds_params(double_sided="Off", Back_Line_1="hello"),
            "off_back_invalid",
        )
        assert _z_max(_trimesh, stl_path) < baseline_z + 1.0, (
            "double_sided Off rendered an INVALID CHARACTERS warning for back "
            "text that never reaches the geometry."
        )

    def test_an_over_capacity_back_line_names_the_field(self, ds_runner, tmp_path):
        capacity = _scad_constant("grid_columns")
        _, output = _render(
            ds_runner,
            tmp_path,
            _ds_params(Back_Line_1=BRAILLE_FULL_CELL * (capacity + 2)),
            "back_too_long",
        )
        assert "WARNING: Back_Line_1 uses" in output, (
            "An over-capacity back line must name Back_Line_1, not send the user "
            f"hunting through the front text.\noutput (truncated): {output[:800]}"
        )

    def test_a_back_line_past_the_grid_names_the_field(self, ds_runner, tmp_path):
        rows = _scad_constant("grid_rows")
        _, output = _render(
            ds_runner,
            tmp_path,
            _ds_params(**{f"Back_Line_{rows + 1}": BACK_TEXT}),
            "back_too_many_rows",
        )
        assert f"WARNING: back text reaches Back_Line_{rows + 1}" in output, (
            "A back line past grid_rows must say so; those rows cannot be drawn "
            f"under any setting.\noutput (truncated): {output[:800]}"
        )

    def test_the_export_hint_names_the_right_cylinder(self, ds_runner, tmp_path):
        """
        Double-sided renders come in pairs and the two STLs have to be told
        apart after export. Deliberately NOT a WARNING line - scad-check.ps1
        treats that token as a failure.
        """
        _, a_out = _render(ds_runner, tmp_path, _ds_params(), "hint_a")
        _, b_out = _render(
            ds_runner, tmp_path, _ds_params(plate_type="negative"), "hint_b"
        )
        assert "this render is Cylinder A" in a_out and "Cylinder_A_" in a_out
        assert "this render is Cylinder B" in b_out and "Cylinder_B_" in b_out
        assert "WARNING:" not in a_out and "WARNING:" not in b_out

    def test_the_lowercase_gate_reaches_the_geometry(self, ds_runner, tmp_path):
        """
        The test system passes -D double_sided='"on"'. It must switch the mode
        on exactly like the Customizer's "On", the way plate_type accepts
        "positive" beside "Embossing Plate".
        """
        _, output = _render(
            ds_runner,
            tmp_path,
            _ds_params(double_sided="on", ds_self_check=True),
            "lowercase_gate",
        )
        assert "DS_PAIR A back_recess" in output, (
            "double_sided='on' did not reach the back-grid walk.\n"
            f"output (truncated): {output[:800]}"
        )


# ---------------------------------------------------------------------------
# Phase 13: cross-validation against the web repo's double-sided golden pair
# ---------------------------------------------------------------------------
#
# The web repo owns `tests/fixtures/ds_cylinderA_golden.stl` / `...B...` and
# their `.json` input records. They are NOT copied here - a second copy would
# drift - so everything below skips when that repo is not on disk beside this
# one. Point BRAILLE_WEB_REPO at it to run these from anywhere.
#
# WHAT THE TWO GENERATORS CAN AND CANNOT SHARE, measured 2026-08-21.
# The golden pair is a SCHEMA-DEFAULT configuration: a solid shell of diameter
# 30.75 mm carrying the Option B footprints. This generator reaches Option B
# only through `paper_thickness_preset = "0.3mm"`, and that preset table also
# carries `cylinder_diameter_mm = 30.8` and `polygon_cutout_radius_mm = 13`,
# which `preset_value()` applies OVER any -D override. So the scad renders the
# same braille on a 0.025 mm larger radius, with a 12-sided mounting bore.
# That is not a defect on either side: the web app's own THICKNESS_PRESETS
# carry the same two numbers, so the preset tables agree; the goldens simply
# predate presets, being cut straight from the schema defaults.
# TestGoldenConfigurationParity pins both halves so neither drifts quietly.
#
# The consequence shapes every comparison below. A different radius turns the
# same ARC into a different ANGLE (6.5 mm of cell spacing is 24.183 deg at
# r=15.4 and 24.222 deg at r=15.375), so positions are compared as SIGNED ARC
# LENGTH, theta * radius, which is what both generators actually lay out. And
# volumes are compared only after each generator's own shell and bore are
# removed, measured from its own top cap so no tessellation constant is assumed.

WEB_REPO_ENV = "BRAILLE_WEB_REPO"
GOLDEN_STEM = {"positive": "ds_cylinderA_golden", "negative": "ds_cylinderB_golden"}
GOLDEN_LABEL = {"positive": "Cylinder A", "negative": "Cylinder B"}
GOLDEN_PACKAGE = "0.3mm"  # the only preset that renders the goldens' Option B dies

# ---- tolerances -----------------------------------------------------------
# Every number here was MEASURED on 2026-08-21 (OpenSCAD 2026.01.03 Manifold,
# trimesh 4.10.1) and is set just wide enough to cover the measurement, with
# each contribution named. Widening one to turn a red test green would throw
# away the only end-to-end parity proof the two generators have.

# POSITIONS. Worst measured arc deviation 0.0068 mm, worst axial 0.0024 mm.
# Both are cluster-centroid noise: the golden's icosphere-3 dome has no vertex
# ring symmetric about the dot axis where OpenSCAD's $fn=32 sphere does, so the
# two vertex clouds have slightly different centres of mass. The smallest
# placement error that could mean anything is the 1.25 mm interpoint step, and
# the tightest spacing in the layout is 2.5 mm, so these sit two to three
# orders of magnitude clear of a real fault.
GOLDEN_ARC_TOL_MM = 0.02
GOLDEN_Z_TOL_MM = 0.01

# FOOTPRINTS. Both generators aim at the same nominal numbers and land just
# under them, because a tessellated dome is inscribed in the ideal one:
#   raised dot proud   scad 0.7981   golden 0.8000   nominal DS_DOT_HEIGHT 0.8
#   bowl cut depth     scad 0.6693   golden 0.6725   nominal DS_BOWL_R  0.6725
# The golden reaches nominal on both because icosphere-3 puts a vertex exactly
# at the pole; OpenSCAD's $fn=32 sphere puts its deepest ring at 84.375 deg of
# latitude and so falls 0.0019 / 0.0032 mm short. 0.005 mm covers that with
# room, and is still far inside the +/-0.1 mm the printer contributes.
GOLDEN_FOOTPRINT_TOL_MM = 0.005

# VOLUMES, after each generator's own shell and bore are removed:
#   Cylinder A features   scad +37.3912   golden +37.7371   delta -0.3459
#   Cylinder B features   scad -69.4277   golden -69.2498   delta -0.1779
# Measured contributions to the Cylinder A delta:
#   -0.1132  5 raised dots, 0.02263 mm^3 each. This generator builds the
#            frustum at cone_segments = 16 and the dome at $fn = 32; the golden
#            uses 48-section frusta and an icosphere at subdivision 3. Both
#            inscribe the ideal solid, the coarser one more deeply.
#   +0.0543  8 bowls, 0.00678 mm^3 each - the same sphere difference with the
#            opposite sign, because a coarser cutter removes less.
#   -0.2447  4 raised seam arrows. The golden generator grows the RAISED arrow
#            outline by 5 um (`_DS_ARROW_WELD_MM`) so the arrow apex cannot weld
#            into the next arrow's base as a non-manifold pinch edge. This
#            generator has no such growth and needs none. Recessed arrows, which
#            neither generator grows, agree to 0.00003 mm^3 once the row-to-row
#            overlap at 10 mm arrows on 10 mm line spacing is accounted for.
#   -0.0422  residue: the golden is quantised to float32 and re-welded on
#            export, and adjacent features overlap slightly on both plates.
# 0.45 mm^3 covers the worse of the two plates with about 30% margin.
GOLDEN_FEATURE_VOLUME_TOL_MM3 = 0.45
# A minus B cancels the shell and the bore EXACTLY - both plates are carved from
# the same solid - leaving 3 dots, 3 bowls and the arrow weld:
#   scad 106.8190   golden 106.9870   delta -0.1680 (-0.157%)
GOLDEN_AB_VOLUME_TOL_MM3 = 0.25


def _web_fixtures_dir():
    """The web repo's fixtures directory, or None when it is not on disk."""
    root = os.environ.get(WEB_REPO_ENV)
    root = Path(root) if root else PROJECT_ROOT.parent / "braille-cylinder-stl-generator"
    fixtures = root / "tests" / "fixtures"
    return fixtures if (fixtures / f"{GOLDEN_STEM['positive']}.stl").exists() else None


@pytest.fixture(scope="module")
def web_fixtures():
    fixtures = _web_fixtures_dir()
    if fixtures is None:
        pytest.skip(
            "The web repo's double-sided goldens were not found. Clone "
            "braille-cylinder-stl-generator beside this repo, or set "
            f"{WEB_REPO_ENV} to it, to run the cross-validation."
        )
    return fixtures


@pytest.fixture(scope="module")
def golden_config(web_fixtures):
    """
    The generation record the two plates share, read first-hand from the
    fixtures' own .json - never from this repo's idea of what they hold.
    """
    records = {
        plate_type: json.loads((web_fixtures / f"{stem}.json").read_text(encoding="utf-8"))
        for plate_type, stem in GOLDEN_STEM.items()
    }
    a = records["positive"]["generation"]
    b = records["negative"]["generation"]
    for key in ("front_lines", "back_lines", "settings", "cylinder_params", "generated"):
        assert a[key] == b[key], (
            f"The golden pair disagrees about `{key}`. A and B must be two sides "
            "of ONE configuration or nothing below is a comparison."
        )
    return a


@pytest.fixture(scope="module")
def golden_meshes(_trimesh, web_fixtures):
    return {
        plate_type: _trimesh.load(web_fixtures / f"{stem}.stl")
        for plate_type, stem in GOLDEN_STEM.items()
    }


@pytest.fixture(scope="module")
def golden_scad_stls(ds_runner, golden_config, tmp_path_factory):
    """This generator's answer to the goldens' inputs, both plates."""
    tmp_path = tmp_path_factory.mktemp("ds_cross_validation")
    settings = golden_config["settings"]
    out = {}
    for plate_type in GOLDEN_STEM:
        stl_path, output = _render(
            ds_runner,
            tmp_path,
            _ds_params(
                plate_type=plate_type,
                paper_thickness_preset=GOLDEN_PACKAGE,
                grid_columns=settings["grid_columns"],
                grid_rows=settings["grid_rows"],
                interpoint_offset_x_mm=settings["interpoint_offset_x"],
                interpoint_offset_y_mm=settings["interpoint_offset_y"],
            ),
            f"golden_config_{plate_type}",
        )
        assert "WARNING:" not in output and "ERROR:" not in output, (
            f"The golden configuration did not render clean on "
            f"{GOLDEN_LABEL[plate_type]}; the Option B package is meant to be "
            f"silent.\noutput (truncated): {output[:800]}"
        )
        out[plate_type] = stl_path
    return out


@pytest.fixture(scope="module")
def golden_scad_layout(golden_config):
    """The layout this generator actually renders at, on ITS preset radius."""
    settings = golden_config["settings"]
    return _layout_from(
        radius=_preset_value("cylinder_diameter_mm", table="PRESET_03") / 2,
        cols=settings["grid_columns"],
        rows=settings["grid_rows"],
        package=GOLDEN_PACKAGE,
        table="PRESET_03",
    )


@pytest.fixture(scope="module")
def golden_web_layout(golden_config):
    """The layout the goldens were cut at, on the schema radius."""
    settings = golden_config["settings"]
    return _layout_from(
        radius=golden_config["cylinder_params"]["diameter"] / 2,
        cols=settings["grid_columns"],
        rows=settings["grid_rows"],
        package=GOLDEN_PACKAGE,
        height=golden_config["cylinder_params"]["height"],
        table="PRESET_03",
    )


@pytest.fixture(scope="module")
def golden_features(_trimesh, golden_scad_stls, web_fixtures,
                    golden_scad_layout, golden_web_layout):
    """Vertex clusters for all four meshes, keyed (source, plate_type)."""
    out = {}
    for plate_type, stem in GOLDEN_STEM.items():
        out[("scad", plate_type)] = _Features(
            _trimesh, golden_scad_stls[plate_type], golden_scad_layout
        )
        out[("golden", plate_type)] = _Features(
            _trimesh, web_fixtures / f"{stem}.stl", golden_web_layout
        )
    return out


def _layout_for(source, scad_layout, web_layout):
    return scad_layout if source == "scad" else web_layout


def _expected_places(layout, plate_type, kind, source):
    """
    Where the interpoint maths puts each feature, in one generator's frame.

    Cylinder A raises the front text and sinks the back grid; Cylinder B is A's
    angle-negation mirror, so it raises the back grid and sinks the front. The
    web generator then mirrors the whole layout again about the seam plane
    (its cylindrical transform runs theta the other way), which is the final
    negation.
    """
    if plate_type == "positive":
        places = (
            _front_placements(layout, FRONT_TEXT)
            if kind == "raised"
            else _back_placements(layout, BACK_TEXT)
        )
    else:
        places = (
            _negated(_back_placements(layout, BACK_TEXT))
            if kind == "raised"
            else _negated(_front_placements(layout, FRONT_TEXT))
        )
    return _negated(places) if source == "golden" else places


def _arcs(features, mask, layout):
    """(signed arc length mm, height mm) of every feature in `mask`."""
    return [
        (math.radians(c["theta"]) * layout["radius"], c["z"])
        for c in features.clusters(mask)
    ]


def _mirrored_arcs(arcs):
    """The seam-plane mirror, in arc-length terms - see `_expected_places`."""
    return [(-arc, z) for arc, z in arcs]


def _pair_arcs(scad_arcs, golden_arcs, label):
    """
    Pair each scad feature with its nearest golden partner, one to one, and
    return the worst arc and height deviation over the whole set.
    """
    assert len(scad_arcs) == len(golden_arcs), (
        f"{label}: this generator rendered {len(scad_arcs)} features, the golden "
        f"holds {len(golden_arcs)}.\n"
        f"scad:   {[(round(a, 3), round(z, 3)) for a, z in sorted(scad_arcs)]}\n"
        f"golden: {[(round(a, 3), round(z, 3)) for a, z in sorted(golden_arcs)]}"
    )
    remaining = list(golden_arcs)
    worst_arc = worst_z = 0.0
    for arc, z in scad_arcs:
        partner = min(remaining, key=lambda g: (arc - g[0]) ** 2 + (z - g[1]) ** 2)
        remaining.remove(partner)
        worst_arc = max(worst_arc, abs(arc - partner[0]))
        worst_z = max(worst_z, abs(z - partner[1]))
    assert worst_arc <= GOLDEN_ARC_TOL_MM and worst_z <= GOLDEN_Z_TOL_MM, (
        f"{label}: worst arc deviation {worst_arc:.5f} mm (limit "
        f"{GOLDEN_ARC_TOL_MM}), worst height deviation {worst_z:.5f} mm (limit "
        f"{GOLDEN_Z_TOL_MM}). The two generators place this feature set "
        "differently - a layout fault, not a tolerance to widen."
    )
    return worst_arc, worst_z


def _prism_volume_from_top_cap(mesh, height, tol=1e-6):
    """
    The volume of the plain shell this mesh was carved from, measured off its
    own top cap.

    Every double-sided feature sits on the curved side, so the flat cap is
    untouched: cap area * height is exactly the shell, less the mounting bore
    where one is cut. Taking it from the mesh means no comparison has to assume
    either generator's segment count.
    """
    import numpy as np

    on_cap = np.abs(mesh.vertices[:, 2] - height) < tol
    faces = on_cap[mesh.faces].all(axis=1)
    assert faces.any(), f"No flat top cap found at z={height}."
    return float(mesh.area_faces[faces].sum()) * height


def _feature_volume(mesh, height):
    """Everything the double-sided pass added to, or took out of, the shell."""
    return float(mesh.volume) - _prism_volume_from_top_cap(mesh, height)


class TestGoldenFixtureRecord:
    """
    The tolerances above were measured against ONE version of the golden pair.
    These read its record first-hand and fail loudly if it is regenerated on
    different inputs, rather than letting a stale tolerance quietly pass.
    """

    def test_the_pair_holds_the_option_b_package(self, golden_config):
        settings = golden_config["settings"]
        expected = {
            "ds_dot_base_diameter": 1.2,
            "ds_dot_base_height": 0.4,
            "ds_dot_dome_diameter": 0.8,
            "ds_dot_dome_height": 0.4,
            "ds_bowl_base_diameter": PACKAGES[GOLDEN_PACKAGE]["bowl_dia"],
            "ds_bowl_depth": _scad_constant("DS_BOWL_DEPTH"),
        }
        actual = {key: settings[key] for key in expected}
        assert actual == expected, (
            f"The golden pair no longer holds the Option B footprints: {actual}. "
            "This repo can only render Option B through paper_thickness_preset "
            f'"{GOLDEN_PACKAGE}", so a pair re-cut on the Q2 package needs the '
            "cross-validation re-pointed and every tolerance re-measured."
        )

    def test_the_bowls_are_cut_centre_on_surface(self, golden_config):
        """
        FD-7(b), 2026-08-19: the browser worker centres the bowl sphere ON the
        shell, so the cut is a hemisphere of radius DS_BOWL_R and ds_bowl_depth
        sets neither the depth nor the mouth. The goldens were regenerated on
        that convention 2026-08-20; on the older exact-depth convention every
        bowl would be 0.17 mm shallower and the footprint tests below would be
        comparing two different parts.
        """
        assert "centre-on-surface" in golden_config["note"], (
            "The golden pair's generation note no longer says the bowls are cut "
            f"centre-on-surface:\n{golden_config['note']}"
        )
        assert golden_config["generated"] >= "2026-08-20", (
            f"The goldens are dated {golden_config['generated']}, before the "
            "2026-08-20 regeneration that put them on the centre-on-surface "
            "bowl convention."
        )

    def test_the_pair_is_the_double_sided_reference_model(self, golden_config):
        settings = golden_config["settings"]
        assert golden_config["front_lines"][0] == FRONT_TEXT
        assert golden_config["back_lines"][0] == BACK_TEXT
        assert settings["indicator_mode"] == "tactile"
        assert settings["double_sided_enabled"] == 1
        assert (settings["interpoint_offset_x"], settings["interpoint_offset_y"]) == (
            _scad_constant("interpoint_offset_x_mm"),
            _scad_constant("interpoint_offset_y_mm"),
        ), "The goldens were cut at a different interpoint offset than this repo defaults to."

    def test_the_goldens_are_solid_shells(self, golden_config, golden_meshes):
        """
        The web renderer refuses a polygonal cutout for these fixtures, so the
        goldens carry no mounting bore. `_prism_volume_from_top_cap` handles
        either case, but the volume figures quoted above assume this one.
        """
        import numpy as np

        radius = golden_config["cylinder_params"]["diameter"] / 2
        height = golden_config["cylinder_params"]["height"]
        for plate_type, mesh in golden_meshes.items():
            v = mesh.vertices
            on_cap = np.abs(v[:, 2] - height) < 1e-6
            r = np.hypot(v[on_cap, 0], v[on_cap, 1])
            assert r.min() < 1e-6, (
                f"The golden {GOLDEN_LABEL[plate_type]} has a hole in its top cap - "
                "it has grown a mounting bore and the volume figures are stale."
            )
            assert r.max() <= radius + 1e-6


class TestGoldenConfigurationParity:
    """
    Which of the goldens' inputs this generator can mirror, and which two it
    cannot. Both halves are pinned: the first so a regression shows up as a
    failure, the second so the divergence stays a recorded fact with a reason
    rather than a surprise inside someone's volume comparison.
    """

    def test_the_preset_carries_its_own_cylinder(self, golden_config):
        """
        `preset_value()` returns the preset table's number whenever the table
        holds the key, so a preset render cannot be talked out of its own
        cylinder. That matches the web app, whose THICKNESS_PRESETS carry the
        same two values; the goldens predate presets entirely.
        """
        assert _preset_value("cylinder_diameter_mm", table="PRESET_03") == 30.8
        assert _preset_value("polygon_cutout_radius_mm", table="PRESET_03") == 13.0
        assert golden_config["cylinder_params"]["diameter"] == 30.75, (
            "The goldens moved off the schema diameter; re-measure the volume "
            "figures, which are quoted for a 0.025 mm radius difference."
        )

    @pytest.mark.slow
    def test_the_overrides_really_are_ignored(self, ds_runner, tmp_path):
        """
        Measured, not assumed: passing both overrides changes nothing, which is
        why the cross-validation fixtures do not bother passing them.
        """
        params = _ds_params(paper_thickness_preset=GOLDEN_PACKAGE)
        plain, _ = _render(ds_runner, tmp_path, params, "preset_plain")
        overridden, _ = _render(
            ds_runner,
            tmp_path,
            dict(params, cylinder_diameter_mm=30.75, polygon_cutout_radius_mm=0),
            "preset_overridden",
        )
        assert plain.read_bytes() == overridden.read_bytes(), (
            "cylinder_diameter_mm / polygon_cutout_radius_mm now reach a preset "
            "render. That is a behaviour change in preset_value(); the golden "
            "cross-validation could then mirror the fixture exactly, and this "
            "test - with the tolerances it explains - should be revisited."
        )

    def test_the_two_layouts_differ_only_in_radius(
        self, golden_config, golden_scad_layout, golden_web_layout
    ):
        settings = golden_config["settings"]
        assert golden_scad_layout["rows"] == settings["grid_rows"]
        assert golden_scad_layout["height"] == golden_web_layout["height"]
        assert golden_scad_layout["line"] == golden_web_layout["line"]
        assert golden_scad_layout["top_margin"] == golden_web_layout["top_margin"]
        assert golden_scad_layout["radius"] != golden_web_layout["radius"], (
            "The two configurations now share a radius. Good news, but the "
            "arc-length comparison and its tolerances were written for a "
            "0.025 mm difference and should be revisited."
        )
        assert (
            abs(golden_scad_layout["start_angle"] * golden_scad_layout["radius"]
                - golden_web_layout["start_angle"] * golden_web_layout["radius"])
            < 1e-9
        ), "The two grids start at different ARC positions, not just different angles."


class TestGoldenPositionParity:
    """
    The parity proof. Every double-sided feature on both plates lands at the
    same arc and the same height in both generators, mirrored about the seam
    plane - the whole claim of the port, and the one thing no clearance number
    or volume total can catch.
    """

    @pytest.mark.parametrize(
        ("plate_type", "kind"),
        [("positive", "raised"), ("positive", "recessed"),
         ("negative", "raised"), ("negative", "recessed")],
    )
    def test_features_land_at_the_same_arc(
        self, golden_features, golden_scad_layout, golden_web_layout, plate_type, kind
    ):
        scad = golden_features[("scad", plate_type)]
        gold = golden_features[("golden", plate_type)]
        worst_arc, worst_z = _pair_arcs(
            _arcs(scad, scad.away_from_seam(getattr(scad, kind)), golden_scad_layout),
            _mirrored_arcs(
                _arcs(gold, gold.away_from_seam(getattr(gold, kind)), golden_web_layout)
            ),
            f"{GOLDEN_LABEL[plate_type]} {kind} features",
        )
        print(
            f"\n{GOLDEN_LABEL[plate_type]} {kind}: worst arc {worst_arc:.5f} mm, "
            f"worst height {worst_z:.5f} mm"
        )

    @pytest.mark.parametrize(
        ("plate_type", "kind"),
        [("positive", "raised"), ("positive", "recessed"),
         ("negative", "raised"), ("negative", "recessed")],
    )
    def test_the_rendered_features_sit_where_the_maths_puts_them(
        self, golden_features, golden_scad_layout, golden_web_layout, plate_type, kind
    ):
        """
        Both meshes are checked against the SAME interpoint walk, each in its
        own frame. Without this the arc comparison could only say the two
        generators agree - including agreeing on a shared mistake.
        """
        for source in ("scad", "golden"):
            layout = _layout_for(source, golden_scad_layout, golden_web_layout)
            features = golden_features[(source, plate_type)]
            _pair_arcs(
                _arcs(features, features.away_from_seam(getattr(features, kind)), layout),
                [
                    (angle * layout["radius"], z)
                    for angle, z in _expected_places(layout, plate_type, kind, source)
                ],
                f"{source} {GOLDEN_LABEL[plate_type]} {kind} vs the interpoint maths",
            )

    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_the_two_generators_mirror_each_other(self, golden_features, plate_type):
        """
        The mirror is not a free parameter chosen to make the arcs line up: the
        web generator's cylindrical transform runs theta the other way, so a
        feature this generator puts left of the seam the golden puts right of
        it. If the two ever agreed on sign WITHOUT a code change, the back text
        would read backwards on the paper.
        """
        for kind in ("raised", "recessed"):
            scad = golden_features[("scad", plate_type)]
            gold = golden_features[("golden", plate_type)]
            scad_side = {
                c["theta"] > 0
                for c in scad.clusters(scad.away_from_seam(getattr(scad, kind)))
            }
            gold_side = {
                c["theta"] > 0
                for c in gold.clusters(gold.away_from_seam(getattr(gold, kind)))
            }
            assert len(scad_side) == 1 and len(gold_side) == 1, (
                f"{GOLDEN_LABEL[plate_type]} {kind}: features straddle the seam plane. "
                "The reference model is deliberately one-sided so this cannot happen."
            )
            assert scad_side != gold_side, (
                f"{GOLDEN_LABEL[plate_type]} {kind}: both generators put these features "
                "on the SAME side of the seam. One of the two cylindrical transforms "
                "has changed sign and the back text will read mirrored."
            )


class TestGoldenFootprintParity:
    """
    The dot stands as proud and the bowl cuts as deep in both generators. These
    are the tactile numbers, which are the accessibility feature.
    """

    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_raised_dots_stand_the_same_height(
        self, golden_features, golden_scad_layout, golden_web_layout, plate_type
    ):
        nominal = PACKAGES[GOLDEN_PACKAGE]["dot_height"]
        proud = {}
        for source in ("scad", "golden"):
            layout = _layout_for(source, golden_scad_layout, golden_web_layout)
            features = golden_features[(source, plate_type)]
            heights = [
                c["r_max"] - layout["radius"]
                for c in features.clusters(features.away_from_seam(features.raised))
            ]
            assert heights, f"No raised dots on the {source} {GOLDEN_LABEL[plate_type]}."
            proud[source] = max(heights)
            assert nominal - GOLDEN_FOOTPRINT_TOL_MM <= min(heights) <= nominal + 1e-9, (
                f"A {source} dot stands {min(heights):.4f} mm proud against a "
                f"{nominal} mm Option B die."
            )
        print(
            f"\n{GOLDEN_LABEL[plate_type]} dot proud: scad {proud['scad']:.4f} mm, "
            f"golden {proud['golden']:.4f} mm"
        )
        assert abs(proud["scad"] - proud["golden"]) <= GOLDEN_FOOTPRINT_TOL_MM

    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_bowls_cut_the_same_hemisphere(
        self, golden_features, golden_scad_layout, golden_web_layout, plate_type
    ):
        """
        The number FD-7(b) turned on. Both generators must cut a hemisphere of
        radius DS_BOWL_R - deeper than DS_BOWL_DEPTH, not equal to it - or they
        are making different parts from one spec.
        """
        bowl_r = (
            (golden_scad_layout["bowl_dia"] / 2) ** 2 + golden_scad_layout["bowl_depth"] ** 2
        ) / (2 * golden_scad_layout["bowl_depth"])
        cut = {}
        for source in ("scad", "golden"):
            layout = _layout_for(source, golden_scad_layout, golden_web_layout)
            features = golden_features[(source, plate_type)]
            depths = [
                layout["radius"] - c["r_min"]
                for c in features.clusters(features.away_from_seam(features.recessed))
            ]
            assert depths, f"No bowls on the {source} {GOLDEN_LABEL[plate_type]}."
            cut[source] = max(depths)
            assert layout["bowl_depth"] < cut[source] <= bowl_r + 1e-9, (
                f"The {source} bowl cuts {cut[source]:.4f} mm, outside "
                f"({layout['bowl_depth']}, {bowl_r:.4f}]. A cut no deeper than "
                "DS_BOWL_DEPTH means the sphere is no longer centred on the surface."
            )
        print(
            f"\n{GOLDEN_LABEL[plate_type]} bowl cut: scad {cut['scad']:.4f} mm, "
            f"golden {cut['golden']:.4f} mm (hemisphere radius {bowl_r:.4f})"
        )
        assert abs(cut["scad"] - cut["golden"]) <= GOLDEN_FOOTPRINT_TOL_MM

    def test_the_seam_arrows_match(
        self, golden_features, golden_scad_layout, golden_web_layout
    ):
        """
        The goldens' record does not list the tactile numbers, so they are
        measured off the meshes rather than assumed: the raised arrow stands
        `tactile_indicator_raise` proud on Cylinder A and the recess cuts
        raise + extra depth into Cylinder B, in both generators.
        """
        raise_mm = golden_scad_layout["arrow_raise"]
        recess = raise_mm + golden_scad_layout["arrow_extra_depth"]
        for source in ("scad", "golden"):
            layout = _layout_for(source, golden_scad_layout, golden_web_layout)
            emboss = golden_features[(source, "positive")]
            counter = golden_features[(source, "negative")]
            np = emboss.np
            seam_a = emboss.raised & (np.abs(np.abs(emboss.theta) - 180.0) < 10.0)
            seam_b = counter.recessed & (np.abs(np.abs(counter.theta) - 180.0) < 10.0)
            assert seam_a.any() and seam_b.any(), f"{source}: the seam arrows are missing."
            assert abs(emboss.r[seam_a].max() - (layout["radius"] + raise_mm)) <= 0.01, (
                f"{source}: the raised arrow does not stand {raise_mm} mm proud."
            )
            depth = layout["radius"] - counter.r[seam_b].min()
            assert recess - 0.01 <= depth <= recess + 0.02, (
                f"{source}: the arrow recess cuts {depth:.3f} mm, not {recess} mm."
            )


class TestGoldenContainmentProbes:
    """
    Position and size agree; this asks the meshes the physical question
    directly - is there material where a die must push, and air where the paper
    must form? Probe points come from the interpoint maths, not from either
    mesh, so both generators are asked the same question independently.

    Every scad mesh here is MULTI-BODY: a raised dot's flat base sits at the
    ideal radius while the 64-gon shell facet under it dips up to 0.0185 mm
    inside, so each dot is its own connected component. That is pre-existing,
    reported in Phase 10, unrelated to double-sided, and owned by its own phase
    after Phase 15. Containment is therefore asked of every body in turn, which
    is correct whether the mesh is one body or seven.
    """

    @staticmethod
    def _solid_at(bodies, layout, arc, z, radial):
        """Is the point `radial` mm from the axis, over this feature, material?"""
        import numpy as np

        theta = arc / layout["radius"]
        point = np.array(
            [[radial * math.cos(theta), radial * math.sin(theta), z + layout["height"] / 2.0]]
        )
        return any(bool(body.contains(point)[0]) for body in bodies)

    @pytest.fixture(scope="class")
    def bodies(self, _trimesh, golden_meshes, golden_scad_stls):
        out = {}
        for plate_type in GOLDEN_STEM:
            out[("golden", plate_type)] = golden_meshes[plate_type].split(only_watertight=False)
            out[("scad", plate_type)] = _trimesh.load(
                golden_scad_stls[plate_type]
            ).split(only_watertight=False)
        return out

    @pytest.mark.parametrize("source", ["scad", "golden"])
    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_every_raised_dot_is_solid_and_ends(
        self, bodies, golden_scad_layout, golden_web_layout, source, plate_type
    ):
        layout = _layout_for(source, golden_scad_layout, golden_web_layout)
        height = layout["dot_height"]
        for angle, z in _expected_places(layout, plate_type, "raised", source):
            arc = angle * layout["radius"]
            assert self._solid_at(
                bodies[(source, plate_type)], layout, arc, z,
                layout["radius"] + 0.75 * height,
            ), (
                f"{source} {GOLDEN_LABEL[plate_type]}: no material at 75% of the die "
                f"height over the dot at arc {arc:.3f} mm, z {z:.3f} mm."
            )
            assert not self._solid_at(
                bodies[(source, plate_type)], layout, arc, z,
                layout["radius"] + 1.15 * height,
            ), (
                f"{source} {GOLDEN_LABEL[plate_type]}: the dot at arc {arc:.3f} mm has "
                f"not ended by {1.15 * height:.3f} mm - it is taller than the die."
            )

    @pytest.mark.parametrize("source", ["scad", "golden"])
    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_every_bowl_is_hollow_with_a_floor_under_it(
        self, bodies, golden_scad_layout, golden_web_layout, source, plate_type
    ):
        layout = _layout_for(source, golden_scad_layout, golden_web_layout)
        bowl_r = ((layout["bowl_dia"] / 2) ** 2 + layout["bowl_depth"] ** 2) / (
            2 * layout["bowl_depth"]
        )
        for angle, z in _expected_places(layout, plate_type, "recessed", source):
            arc = angle * layout["radius"]
            assert not self._solid_at(
                bodies[(source, plate_type)], layout, arc, z,
                layout["radius"] - 0.5 * bowl_r,
            ), (
                f"{source} {GOLDEN_LABEL[plate_type]}: solid at half the bowl depth over "
                f"the recess at arc {arc:.3f} mm, z {z:.3f} mm - the bowl was not cut, "
                "or a later union filled it back in."
            )
            assert self._solid_at(
                bodies[(source, plate_type)], layout, arc, z,
                layout["radius"] - bowl_r - 0.15,
            ), (
                f"{source} {GOLDEN_LABEL[plate_type]}: no material under the bowl floor "
                f"at arc {arc:.3f} mm - the recess has cut through the wall."
            )

    @pytest.mark.parametrize("source", ["scad", "golden"])
    def test_the_seam_arrows_probe_both_ways(
        self, bodies, golden_scad_layout, golden_web_layout, source
    ):
        layout = _layout_for(source, golden_scad_layout, golden_web_layout)
        raise_mm = layout["arrow_raise"]
        recess = raise_mm + layout["arrow_extra_depth"]
        seam_arc = math.pi * layout["radius"]
        for row in range(int(layout["rows"])):
            z = _row_y(layout, row)
            assert self._solid_at(
                bodies[(source, "positive")], layout, seam_arc, z,
                layout["radius"] + 0.5 * raise_mm,
            ), f"{source} Cylinder A: row {row}'s raised arrow is hollow at half its raise."
            assert not self._solid_at(
                bodies[(source, "positive")], layout, seam_arc, z,
                layout["radius"] + raise_mm + 0.1,
            ), f"{source} Cylinder A: row {row}'s arrow stands taller than {raise_mm} mm."
            assert not self._solid_at(
                bodies[(source, "negative")], layout, seam_arc, z,
                layout["radius"] - 0.5 * recess,
            ), f"{source} Cylinder B: row {row}'s arrow recess is solid at half depth."
            assert self._solid_at(
                bodies[(source, "negative")], layout, seam_arc, z,
                layout["radius"] - recess - 0.15,
            ), f"{source} Cylinder B: row {row}'s arrow recess has cut through the wall."


class TestGoldenVolumeParity:
    """
    Whole-mesh volumes, once each generator's own shell and mounting bore are
    removed. The tolerance block above lists every measured contribution and
    where it comes from.
    """

    @pytest.mark.parametrize("plate_type", list(GOLDEN_STEM))
    def test_feature_volume_matches(
        self, _trimesh, golden_scad_stls, golden_meshes, golden_config,
        golden_scad_layout, plate_type
    ):
        height = golden_config["cylinder_params"]["height"]
        assert height == golden_scad_layout["height"], (
            "The two configurations no longer share a cylinder height; the top-cap "
            "shell measurement assumes they do."
        )
        scad = _feature_volume(_trimesh.load(golden_scad_stls[plate_type]), height)
        gold = _feature_volume(golden_meshes[plate_type], height)
        print(
            f"\n{GOLDEN_LABEL[plate_type]} feature volume: scad {scad:+.4f} mm^3, "
            f"golden {gold:+.4f} mm^3, delta {scad - gold:+.4f} mm^3"
        )
        assert abs(scad - gold) <= GOLDEN_FEATURE_VOLUME_TOL_MM3, (
            f"{GOLDEN_LABEL[plate_type]}: the double-sided features differ by "
            f"{scad - gold:+.4f} mm^3, past the {GOLDEN_FEATURE_VOLUME_TOL_MM3} mm^3 "
            "that the measured tessellation and weld differences account for. "
            "Something geometric has moved - do not widen this without re-measuring "
            "the contributions listed above it."
        )

    def test_the_a_minus_b_difference_matches(
        self, _trimesh, golden_scad_stls, golden_meshes
    ):
        """
        The tightest volume check available, because it needs no shell figure at
        all: both plates are carved from the SAME solid, so subtracting one from
        the other cancels the shell and the mounting bore exactly and leaves
        3 dots, 3 bowls and the arrow weld.
        """
        scad = float(_trimesh.load(golden_scad_stls["positive"]).volume) - float(
            _trimesh.load(golden_scad_stls["negative"]).volume
        )
        gold = float(golden_meshes["positive"].volume) - float(
            golden_meshes["negative"].volume
        )
        print(
            f"\nA - B: scad {scad:.4f} mm^3, golden {gold:.4f} mm^3, "
            f"delta {scad - gold:+.4f} mm^3"
        )
        assert abs(scad - gold) <= GOLDEN_AB_VOLUME_TOL_MM3, (
            f"A minus B differs by {scad - gold:+.4f} mm^3 between the generators, "
            f"past the {GOLDEN_AB_VOLUME_TOL_MM3} mm^3 tessellation accounts for. "
            "The shell cancels out of this figure, so the fault is in the features."
        )


class TestGoldenTopology:
    """
    What the meshes are made of. Watertightness is RECORDED for Cylinder A
    rather than asserted: the web worker's raised-arrow output is known to carry
    pinch edges at the seam where an arrow apex meets the next arrow's base, so
    a red bar there would report a known upstream condition rather than a fault
    in this port. Measured 2026-08-21: all four meshes come out watertight - the
    goldens because their generator grows the raised outline by 5 um and rewelds
    on export, this generator because it never creates the tangency.
    """

    def test_cylinder_b_and_both_goldens_are_watertight(
        self, _trimesh, golden_scad_stls, golden_meshes
    ):
        for plate_type, mesh in golden_meshes.items():
            assert mesh.is_watertight, (
                f"The golden {GOLDEN_LABEL[plate_type]} is not watertight; the "
                "fixture itself is damaged."
            )
        counter = _trimesh.load(golden_scad_stls["negative"])
        assert counter.is_watertight, (
            "Cylinder B stopped being watertight. It has no raised arrows, so it "
            "has no excuse - this is a real regression."
        )
        emboss = _trimesh.load(golden_scad_stls["positive"])
        print(f"\nCylinder A watertight (recorded, not asserted): {emboss.is_watertight}")

    def test_the_scad_dots_are_still_separate_bodies(
        self, _trimesh, golden_scad_stls, golden_meshes
    ):
        """
        Pins the known floating-dot artefact so its eventual fix is visible
        rather than silent: one shell plus one body per RAISED dot - 5 front
        dots on Cylinder A, 8 back dots on Cylinder B. The goldens are single
        bodies because their generator sinks a 0.05 mm skirt into the shell.
        """
        for plate_type, raised in (("positive", EXPECTED_FRONT_DOTS),
                                   ("negative", EXPECTED_BACK_BOWLS)):
            bodies = _trimesh.load(golden_scad_stls[plate_type]).split(only_watertight=False)
            assert len(bodies) == 1 + raised, (
                f"{GOLDEN_LABEL[plate_type]} split into {len(bodies)} bodies, not the "
                f"{1 + raised} the floating-dot artefact produces (1 shell + {raised} "
                "raised dots). If the dots have been sunk into the shell, that is the "
                "fix landing and this count should become 1."
            )
            assert len(golden_meshes[plate_type].split(only_watertight=False)) == 1


BACKWARD_COMPAT_CASES = (
    "cylinder_rounded_emboss_indicators_on",
    "cylinder_rounded_counter_indicators_on",
)


def _cross_platform_params(fixtures_dir, case_name):
    cases = json.loads((fixtures_dir / "test_cases.json").read_text(encoding="utf-8"))
    for case in cases["test_cases"]:
        if case["name"] == case_name:
            return case["parameters"]
    raise AssertionError(f"No cross-platform test case named {case_name}")


class TestBackwardCompatWithDoubleSidedOff:
    """
    With the gate Off the single-sided plates still match the committed
    web-generator reference meshes, at this repo's own comparison level
    (tests/compare_config.json).

    TestDoubleSidedOffIsInert proves that toggling the gate off is
    byte-identical to never having had the feature. This is the other half of
    that claim: what BOTH of those render is still the geometry the
    cross-platform fixtures were cut from. It drives the same fixture
    parameters as tests/cross_platform_validation.py, which pytest never
    collects - that file is not named test_*.py - so until now nothing in the
    default suite compared a render against a reference mesh.
    """

    @pytest.mark.slow
    @pytest.mark.parametrize("case_name", BACKWARD_COMPAT_CASES)
    def test_matches_the_reference_fixture(
        self, case_name, ds_runner, mesh_comparator, fixtures_dir, tmp_path
    ):
        reference = fixtures_dir / case_name / "reference.stl"
        if not reference.exists():
            pytest.skip(f"Reference fixture not found: {reference}")
        params = dict(_cross_platform_params(fixtures_dir, case_name), double_sided="Off")
        stl_path, output = _render(ds_runner, tmp_path, params, case_name)
        assert "WARNING:" not in output and "ERROR:" not in output, (
            f"{case_name} no longer renders clean.\noutput (truncated): {output[:800]}"
        )
        result = mesh_comparator.compare(reference, stl_path)
        assert result.passed, (
            f"{case_name} no longer matches its reference mesh with double_sided "
            "Off:\n  " + "\n  ".join(result.failures)
        )
