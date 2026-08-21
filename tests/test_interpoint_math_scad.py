"""
Double-sided (interpoint) math tests for the DOUBLE-SIDED MATH section of
``Braille_Cylinder_STL_Generator.scad``.

That section is a port of the web generator's ``app/geometry/interpoint.py``,
which stays the authoritative implementation. Nothing in it draws geometry yet:
it is constants, two pure functions, five echoed self-checks and three range
guards, all reached only through hidden parameters. So the way to test it is to
render the model and read what it printed.

Two kinds of test live here:

* **Render tests** run OpenSCAD. ``-D ds_self_check=true`` turns on the five
  ``ECHO: "DS_SELFCHECK <key>=<value>"`` lines and this file asserts every one of
  them to +/-0.001 mm. Two more renders prove the guards behave: an out-of-range
  interpoint offset must FAIL the render (that is the whole point of an assert in
  this repo - a failed assert fails ``scripts\\scad-check.ps1``), and the shipped
  defaults must render clean. These skip when no OpenSCAD binary is available,
  which is the expected outcome in the ``test-quick`` CI job.
* **Source guards** read the .scad as text and run everywhere, including the
  no-OpenSCAD job. They pin the signed-off tactile numbers and the placement of
  the block.

ECHO goes to stderr on ``openscad.exe`` and to stdout on ``openscad.com``, so the
two streams are always read together.

License: PolyForm Noncommercial 1.0.0
"""

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

# Tolerance the phase brief sets for every self-check value, in mm. OpenSCAD's
# echo prints 6 significant figures, so the printed number differs from the exact
# one in the 6th figure at worst - three orders of magnitude inside this bound.
TOLERANCE_MM = 0.001

# The five self-check values, in mm, from app/geometry/interpoint.py.
#
#   lattice_1_25_1_25  lattice_min_center_distance(1.25, 1.25) = 1.25 * sqrt(2).
#                      The signed-off D1 diagonal offset, and the maximum the
#                      2.5 / 6.5 / 10.0 lattice allows.
#   lattice_1_25_0     the same offset with no axial step: the diagonal collapses
#                      onto the circumferential pitch and the distance drops to
#                      the bare 1.25 mm. This is why the offset is diagonal.
#   gap_package_03     same_surface_min_gap for the 0.3-preset package
#                      (Option B: dot 1.2, bowl 1.3). Above the 0.50 mm
#                      reliable threshold - comfortably printable.
#   gap_package_04     the 0.4-preset package (Q2: dot 1.2, bowl 1.4).
#                      Below the reliable line BY DESIGN - the printed
#                      0.428 mm ridge was measured clean 2026-08-20 - and
#                      above the 0.34 mm floor.
#   gap_active         the same gap for the ACTIVE preset's package; the
#                      shipped default preset is 0.4mm, so this equals
#                      gap_package_04.
#   gap_active_printed the SAME gap measured on the bowl's PRINTED mouth
#                      (2 * DS_BOWL_R) rather than its nominal diameter. The
#                      bowl is a hemisphere centred on the surface, so the
#                      mouth is wider than DS_BOWL_DIA and the real ridge is
#                      narrower than every nominal gap above - 0.428 mm at the
#                      default preset against the nominal 0.468. Reported only:
#                      the DOTS TOO CLOSE warning and the render guard still
#                      measure the nominal, as all three generators do. Pinned
#                      here so the understatement stays visible and measured
#                      while the threshold decision is open (Phase 12 sign-off).
#   gap_single_sided   the same gap for the web app's single-sided sizes
#                      (dot 1.5, bowl 1.8). The documented failure case: below
#                      the 0.34 mm floor a 0.4 mm nozzle can hold.
#   gap_legacy_cone    the legacy cone footprints (1.8, 1.8). Negative, meaning
#                      the two footprints overlap outright.
EXPECTED_MM = {
    "lattice_1_25_1_25": 1.767767,
    "lattice_1_25_0": 1.250,
    "gap_package_03": 0.518,
    "gap_package_04": 0.468,
    "gap_active": 0.468,
    "gap_active_printed": 0.428,
    "gap_single_sided": 0.118,
    "gap_legacy_cone": -0.032,
}

# ECHO: "DS_SELFCHECK <key>=<value>". The header line prints "DS_SELFCHECK:"
# with no space before the colon, so it cannot match.
SELF_CHECK_RE = re.compile(r"DS_SELFCHECK\s+(\w+)=(-?[\d.]+(?:[eE][-+]?\d+)?)")

# Everything from this marker to EOF must stay byte-identical to the MakerWorld
# flattened build (tests/test_makerworld_sync.py), which is re-flattened in its
# own phase. The double-sided block therefore has to sit above it.
BODY_MARKER = "// BACKWARD COMPATIBILITY - Test System Parameters"
DS_SECTION_MARKER = "// DOUBLE-SIDED (INTERPOINT) MATH"


@pytest.fixture(scope="module")
def scad_source():
    return SCAD_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def scad_runner():
    """
    Module-scoped OpenSCAD runner preferring the nightly install, the same way
    the warning render tests resolve it.
    """
    from openscad_runner import OpenSCADNotFoundError, OpenSCADRunner

    try:
        return OpenSCADRunner(openscad_path=_resolve_openscad_path())
    except OpenSCADNotFoundError as exc:
        pytest.skip(f"OpenSCAD not available for the interpoint math tests: {exc}")


def _render(scad_runner, tmp_path, params, name):
    """
    Render once and return (result, combined_output).

    Unlike the other render helpers here this does NOT assert success: two of
    these tests are about a render that must fail.
    """
    result = scad_runner.generate_stl(
        scad_file=SCAD_FILE,
        output_stl=tmp_path / f"{name}.stl",
        parameters=params,
        timeout_seconds=180,
    )
    return result, (result.stdout or "") + "\n" + (result.stderr or "")


class TestSelfCheckValues:
    """The five echoed values reproduce interpoint.py to +/-0.001 mm."""

    @pytest.fixture(scope="class")
    def self_check_values(self, scad_runner, tmp_path_factory):
        """
        Render once with the self-checks on and return {key: float}.

        ``double_sided`` deliberately stays Off: the maths is pure, so it is
        checked independently of the feature gate.
        """
        tmp_path = tmp_path_factory.mktemp("interpoint_self_check")
        result, output = _render(
            scad_runner, tmp_path, {"ds_self_check": True}, "self_check"
        )
        assert result.success, (
            "OpenSCAD failed to render the interpoint self-check\n"
            f"returncode={result.returncode}\n"
            f"output (truncated): {output[:800]}"
        )
        values = {key: float(raw) for key, raw in SELF_CHECK_RE.findall(output)}
        assert values, (
            "No DS_SELFCHECK echo lines found. ds_self_check did not reach the "
            f"self-check block, or its labels changed.\noutput: {output[:800]}"
        )
        return values

    def test_every_expected_value_is_echoed(self, self_check_values):
        missing = sorted(set(EXPECTED_MM) - set(self_check_values))
        assert not missing, (
            f"Self-check keys missing from the render: {missing}. Every value in "
            "EXPECTED_MM must be echoed, or the maths behind it is untested."
        )

    @pytest.mark.parametrize("key", sorted(EXPECTED_MM))
    def test_value_matches_interpoint_py(self, key, self_check_values):
        actual = self_check_values[key]
        expected = EXPECTED_MM[key]
        assert abs(actual - expected) <= TOLERANCE_MM, (
            f"{key}: .scad echoed {actual} mm, app/geometry/interpoint.py gives "
            f"{expected} mm (tolerance +/-{TOLERANCE_MM} mm). The two "
            "implementations have diverged; interpoint.py is authoritative."
        )

    def test_the_axial_step_is_what_buys_the_clearance(self, self_check_values):
        """
        The diagonal offset is not decoration: dropping the axial component
        collapses the front-to-back distance to the bare circumferential pitch.
        """
        assert (
            self_check_values["lattice_1_25_0"]
            < self_check_values["lattice_1_25_1_25"]
        )

    def test_both_packages_clear_the_floor_and_the_others_do_not(self, self_check_values):
        """
        The reason double-sided mode ships its own smaller footprints: at the
        single-sided sizes the same-surface gap falls under the 0.34 mm a 0.4 mm
        nozzle can print, and the legacy cone sizes overlap outright. The 0.3
        package clears the RELIABLE line; the 0.4 package is marginal by design
        but clears the floor.
        """
        assert self_check_values["gap_package_03"] >= 0.50
        assert self_check_values["gap_package_04"] >= 0.34
        assert self_check_values["gap_single_sided"] < 0.34
        assert self_check_values["gap_legacy_cone"] < 0

    def test_the_printed_ridge_is_narrower_than_the_nominal_gap(self, self_check_values):
        """
        Every gap above is measured on the NOMINAL bowl diameter, but the bowl
        is cut as a hemisphere centred on the shell surface, so its printed
        mouth is 2 * DS_BOWL_R - wider. The nominal numbers therefore OVERSTATE
        the material actually left between a raised dot and its neighbouring
        recess, in all three generators alike.

        This is a reported measurement, not a threshold: the printed ridge still
        clears the 0.34 mm floor at the shipped defaults (0.428 mm, measured
        printing clean 2026-08-20). Whether the warning should move onto it is a
        physical decision that has to change both repos together.
        """
        printed = self_check_values["gap_active_printed"]
        nominal = self_check_values["gap_active"]
        assert printed < nominal, (
            f"The printed ridge ({printed} mm) should be narrower than the "
            f"nominal gap ({nominal} mm); the bowl's printed mouth is 2 * "
            "DS_BOWL_R, which is wider than DS_BOWL_DIA."
        )
        assert printed >= 0.34, (
            f"The printed ridge is {printed} mm, below the 0.34 mm a 0.4 mm "
            "nozzle can hold. The shipped footprints would not print."
        )


class TestGuards:
    """The asserts fire when they should, and stay silent when they should."""

    @pytest.mark.parametrize("axis", ["x", "y"])
    def test_out_of_range_offset_fails_the_render(self, scad_runner, tmp_path, axis):
        """
        1.05 mm is below the 1.15 mm minimum. A failed assert must stop the
        render and write no STL - that is what makes scad-check.ps1 catch it.
        """
        param = f"interpoint_offset_{axis}_mm"
        result, output = _render(
            scad_runner,
            tmp_path,
            {"double_sided": "On", param: 1.05},
            f"offset_{axis}_out_of_range",
        )
        assert not result.success, (
            f"{param}=1.05 rendered successfully. The range guard did not fire, "
            "so an unprintable pair would export silently."
        )
        assert f"{param} outside 1.15-1.35 range" in output, (
            f"Render failed but not on the {param} range assert.\n"
            f"output (truncated): {output[:800]}"
        )

    def test_defaults_render_clean_with_double_sided_on(self, scad_runner, tmp_path):
        """The shipped 1.25 / 1.25 offset must pass every guard."""
        result, output = _render(
            scad_runner, tmp_path, {"double_sided": "On"}, "double_sided_on"
        )
        assert result.success, (
            "The shipped double-sided defaults failed to render.\n"
            f"returncode={result.returncode}\n"
            f"output (truncated): {output[:800]}"
        )
        assert "ERROR:" not in output, f"Render reported an error:\n{output[:800]}"


class TestSourceGuards:
    """Text-only checks, so they still run in the no-OpenSCAD CI job."""

    def test_block_sits_above_the_makerworld_sync_marker(self, scad_source):
        """
        The geometry body from BODY_MARKER to EOF must stay byte-identical to the
        MakerWorld flattened build. Moving this block below the marker breaks
        that guard until the MakerWorld file is re-flattened.
        """
        assert DS_SECTION_MARKER in scad_source, "DOUBLE-SIDED MATH section missing"
        assert scad_source.index(DS_SECTION_MARKER) < scad_source.index(BODY_MARKER)

    @pytest.mark.parametrize(
        "name,value",
        [
            # Footprint values SHARED by both preset-keyed packages (FD-8/FD-9,
            # 2026-08-20). The four per-package values are guarded by
            # test_keyed_footprint_holds_both_packages below. Tactile geometry
            # is the accessibility feature: these move only by a deliberate,
            # approved decision, never as a side effect.
            ("DS_DOT_BASE_DIA", 1.2),
            ("DS_BOWL_DEPTH", 0.5),
            # D1 offset range, and the printability thresholds behind the guard.
            ("DS_OFFSET_MIN_MM", 1.15),
            ("DS_OFFSET_MAX_MM", 1.35),
            ("DS_GAP_RELIABLE", 0.50),
            ("DS_GAP_FLOOR", 0.34),
            ("DS_AXIAL_STEP", 1.25),
            # D3 sign. Flipping it is a legitimate fix if a printed pair crowds
            # the wrong side of the arrow - but it must be a deliberate edit.
            ("DS_BACK_DIRECTION", 1),
        ],
    )
    def test_signed_off_constant_holds_its_value(self, scad_source, name, value):
        match = re.search(rf"^{name}\s*=\s*(-?[\d.]+)\s*;", scad_source, re.MULTILINE)
        assert match, f"{name} not declared at the top level of the .scad"
        assert float(match.group(1)) == pytest.approx(value), (
            f"{name} is {match.group(1)}, expected {value}. This number was "
            "signed off in the 2026-08-16 interpoint research; change it only "
            "with an approved decision, and update the specs in the same change."
        )

    @pytest.mark.parametrize(
        ("name", "package_03", "package_04"),
        [
            ("DS_DOT_BASE_H", 0.4, 0.5),
            ("DS_DOT_DOME_DIA", 0.8, 1.0),
            ("DS_DOT_DOME_H", 0.4, 0.5),
            ("DS_BOWL_DIA", 1.3, 1.4),
        ],
    )
    def test_keyed_footprint_holds_both_packages(
        self, scad_source, name, package_03, package_04
    ):
        """
        FD-8/FD-9 (2026-08-20): two fixed packages keyed to
        paper_thickness_preset - "0.3mm" is Option B, anything else the Q2
        print-matrix winner. Tactile geometry is the accessibility feature:
        these move only by a deliberate, approved decision.
        """
        match = re.search(
            rf"^{name}\s*=\s*ds_use_03_package\s*\?\s*(-?[\d.]+)\s*:\s*(-?[\d.]+)\s*;",
            scad_source,
            re.MULTILINE,
        )
        assert match, f"{name} is not keyed on ds_use_03_package at the top level"
        assert float(match.group(1)) == pytest.approx(package_03)
        assert float(match.group(2)) == pytest.approx(package_04)

    def test_double_sided_defaults_off(self, scad_source):
        """Toggle-off behavior is the single-sided behavior, so Off is the default."""
        assert re.search(r'^double_sided\s*=\s*"Off"\s*;', scad_source, re.MULTILINE)

    def test_self_check_is_off_by_default(self, scad_source):
        """A plain scad-check must stay quiet."""
        assert re.search(r"^ds_self_check\s*=\s*false\s*;", scad_source, re.MULTILINE)

    def test_dot_map_matches_the_geometry_section(self, scad_source):
        """
        DS_DOT_MAP and dot_positions are the same fixed map of dots 1-6, kept in
        two places only because they sit either side of the MakerWorld marker.
        """
        expected = "[[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]]"
        assert f"DS_DOT_MAP = {expected};" in scad_source
        assert f"dot_positions         = {expected};" in scad_source
