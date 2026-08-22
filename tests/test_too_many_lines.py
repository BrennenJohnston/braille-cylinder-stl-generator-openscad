"""
"TOO MANY LINES" Warning + Ten-Line Wiring Tests

The generator renders only the first ``grid_rows`` rows. Before this warning
existed, braille pasted into a line past that limit simply never appeared:
no console message, nothing on the model, no clue that the file being exported
was missing text. The web app blocks that case outright; OpenSCAD's Customizer
cannot, so the .scad reports it instead — an ``echo()`` for desktop users and a
red extrusion above the cylinder for the MakerWorld preview, which has no
console.

Unlike TEXT TOO LONG, this warning is NOT gated on ``text_limit_check``: rows
past the grid cannot be drawn under any setting, so there is no bypass to
offer.

The render test mirrors ``test_text_too_long.py``: two STLs are compared by
bounding-box Z-max, and it skips when no OpenSCAD binary is available (the
expected outcome in the ``test-quick`` CI job). The source guards below run
everywhere and also pin the Line_1..Line_10 wiring the warning depends on.

License: PolyForm Noncommercial 1.0.0
"""

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
MAKERWORLD_FILE = (
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad"
)

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import (  # noqa: E402  (shared helpers)
    BRAILLE_FULL_CELL,
    _baseline_params,
    _render,
    _scad_constant,
    _z_max,
)

# Every row the grid_rows slider allows must have a Line_N field to fill it.
NUM_LINES = 10

# Rows 9 and 10 live in their own Customizer tab: the Customizer cannot add
# fields on demand, so a separate group is the only way to keep the default
# view at 8 fields while still reaching the slider maximum.
ADVANCED_GROUP = "/* [More Braille Lines (Advanced)] */"


@pytest.fixture(scope="module")
def scad_source():
    return SCAD_FILE.read_text(encoding="utf-8")


class TestTenLines:
    """Every row grid_rows allows is reachable from the Customizer."""

    def test_all_line_parameters_declared(self, scad_source):
        missing = [
            f"Line_{n}"
            for n in range(1, NUM_LINES + 1)
            if not re.search(rf"^Line_{n}\s*=\s*\"", scad_source, re.MULTILINE)
        ]
        assert not missing, (
            f"Missing Line_N declarations: {missing}. grid_rows allows "
            f"{NUM_LINES} rows, so all {NUM_LINES} fields must exist."
        )

    def test_all_lines_list_is_the_single_source_of_truth(self, scad_source):
        match = re.search(r"_all_lines\s*=\s*\[([^\]]+)\]", scad_source)
        assert match, "_all_lines assignment not found"
        listed = [item.strip() for item in match.group(1).replace("\n", " ").split(",")]
        assert listed == [f"Line_{n}" for n in range(1, NUM_LINES + 1)], (
            f"_all_lines must be exactly Line_1..Line_{NUM_LINES} in row order, "
            f"got: {listed}"
        )

    def test_no_line_n_referenced_outside_declarations(self, scad_source):
        """
        Capacity checks, warnings, and the dot loop must all read _all_lines.
        A stray Line_N reference is how a row silently stops being counted.
        """
        code = re.sub(r"_all_lines\s*=\s*\[[^\]]+\]", "", scad_source)
        code = re.sub(r"^Line_\d+\s*=\s*\"[^\"]*\";.*$", "", code, flags=re.MULTILINE)
        code = re.sub(r"^\s*//.*$", "", code, flags=re.MULTILINE)  # prose in comments
        stray = sorted(set(re.findall(r"\bLine_\d+\b", code)))
        assert not stray, (
            f"Line_N referenced outside its declaration and _all_lines: {stray}. "
            "Iterate _all_lines instead."
        )

    def test_first_eight_lines_are_in_the_main_text_group(self, scad_source):
        main_group = scad_source.index("/* [Text Input - Pre-Translated Braille] */")
        advanced_group = scad_source.index(ADVANCED_GROUP)
        main_section = scad_source[main_group:advanced_group]
        for n in range(1, 9):
            assert re.search(rf"^Line_{n}\s*=", main_section, re.MULTILINE), (
                f"Line_{n} must be in the main text input group so eight rows "
                "are visible without opening the Advanced tab."
            )

    def test_last_two_lines_are_in_the_advanced_group(self, scad_source):
        advanced_start = scad_source.index(ADVANCED_GROUP)
        next_group = scad_source.index("/* [", advanced_start + len(ADVANCED_GROUP))
        advanced_section = scad_source[advanced_start:next_group]
        for n in (9, 10):
            assert re.search(rf"^Line_{n}\s*=", advanced_section, re.MULTILINE), (
                f"Line_{n} must be in {ADVANCED_GROUP} — the Customizer cannot "
                "add fields on demand, so the extra rows go in their own tab."
            )

    def test_grid_rows_slider_matches_the_line_count(self, scad_source):
        match = re.search(
            r"^grid_rows\s*=\s*\d+\s*;\s*//\s*\[(\d+):(\d+):(\d+)\]",
            scad_source,
            re.MULTILINE,
        )
        assert match, "grid_rows slider declaration not found"
        assert match.group(3) == str(NUM_LINES), (
            f"grid_rows slider max must be {NUM_LINES} to match the Line_N "
            f"field count, got {match.group(3)}"
        )

    def test_makerworld_build_declares_the_same_lines(self):
        """
        The line declarations sit above the byte-identical geometry body, so
        test_makerworld_sync.py cannot catch a MakerWorld copy that is missing
        the extra fields while its body still reads all ten.
        """
        makerworld = MAKERWORLD_FILE.read_text(encoding="utf-8")
        missing = [
            f"Line_{n}"
            for n in range(1, NUM_LINES + 1)
            if not re.search(rf"^Line_{n}\s*=\s*\"", makerworld, re.MULTILINE)
        ]
        assert not missing, f"MakerWorld build is missing declarations: {missing}"
        assert ADVANCED_GROUP in makerworld, (
            f"MakerWorld build is missing the {ADVANCED_GROUP} Customizer tab"
        )


def test_warning_source_constants_present(scad_source):
    """
    Cheap source-only guard so the `test-quick` CI job (no OpenSCAD installed)
    still catches the warning being dropped or unstacked.
    """
    assert '"TOO MANY LINES: "' in scad_source, (
        'Expected the counted literal `"TOO MANY LINES: "` in the SCAD source'
    )
    assert "too_many_rows = rows_used > active_grid_rows" in scad_source, (
        "Expected too_many_rows to compare the deepest filled row against "
        "active_grid_rows (the preset-routed value, not the raw slider)."
    )
    assert "INVALID_TEXT_Z_OFFSET + 3 * INVALID_TEXT_STACK_GAP" in scad_source, (
        "Expected TOO MANY LINES to sit one stack step above TACTILE GAP TOO "
        "SMALL. Overlapping warnings render as unreadable mush."
    )


def test_row_warning_is_not_gated_on_text_limit_check(scad_source):
    """
    text_limit_check exists so a user can render past the *cell* capacity. No
    such escape hatch exists for rows — they cannot be drawn at all — so the
    row warning must fire regardless of the toggle.
    """
    body = scad_source[scad_source.index("if (too_many_rows)") :]
    guard = body[: body.index("grid_height =")]
    assert "text_limit_check" not in guard, (
        "The TOO MANY LINES echo must not be gated on text_limit_check; extra "
        "rows are dropped whatever it is set to."
    )


@pytest.mark.slow
def test_too_many_lines_emits_warning_extrusion(
    warning_runner, _trimesh, warning_offsets, tmp_path
):
    """
    Filling a row past grid_rows must raise the bounding box by at least one
    warning depth; keeping every filled row within grid_rows must not.
    """
    fits_params = _baseline_params()
    grid_rows = fits_params["grid_rows"]  # 4

    # Deepest filled row == grid_rows: the last row that still renders.
    fits_params[f"Line_{grid_rows}"] = BRAILLE_FULL_CELL * 3

    # One row past the grid: nothing would be drawn for it, hence the warning.
    overflow_params = dict(fits_params)
    overflow_params[f"Line_{grid_rows + 1}"] = BRAILLE_FULL_CELL * 3

    fits_stl = _render(warning_runner, tmp_path, fits_params, "rows_fit")
    overflow_stl = _render(warning_runner, tmp_path, overflow_params, "rows_overflow")

    z_fits = _z_max(_trimesh, fits_stl)
    z_overflow = _z_max(_trimesh, overflow_stl)

    cyl_top = fits_params["cylinder_height_mm"]
    z_offset = warning_offsets["z_offset"]
    depth = warning_offsets["depth"]
    stack_gap = _scad_constant("INVALID_TEXT_STACK_GAP")
    expected_warning_top = cyl_top + z_offset + 3 * stack_gap + depth / 2

    assert z_fits < cyl_top + 2.0, (
        f"Filling exactly grid_rows ({grid_rows}) rows must not warn, but the "
        f"render has geometry above the cylinder: z_max={z_fits:.3f}, "
        f"cylinder_top={cyl_top:.3f}."
    )
    assert z_overflow >= z_fits + depth, (
        f"Filling Line_{grid_rows + 1} with grid_rows={grid_rows} did not raise "
        f"the bounding box by INVALID_TEXT_DEPTH ({depth} mm): z_fits="
        f"{z_fits:.3f}, z_overflow={z_overflow:.3f}. The TOO MANY LINES "
        f"warning may have failed to fire — which is the silent truncation "
        f"this whole check exists to prevent."
    )
    assert z_overflow >= expected_warning_top - 1.0, (
        f"Overflow render's z_max ({z_overflow:.3f}) is below the expected "
        f"warning top ({expected_warning_top:.3f}). Either the warning didn't "
        f"fire or its stack offset drifted."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
