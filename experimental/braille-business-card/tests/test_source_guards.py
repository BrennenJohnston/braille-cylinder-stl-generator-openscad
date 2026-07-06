"""
Source Invariant Guards for the Braille Wedge Card Generator

These tests read the .scad source (no OpenSCAD required) and pin down the
invariants that keep this project on-mission:

1. All 20 Line_N parameters exist and are wired into _all_lines.
2. The grid_rows slider reaches 20.
3. Warning geometry stays preview-only (wrapped in the `%` modifier) so it can
   never fuse into an exported STL.
4. MISSION GUARD: this is a pure directly-readable braille card. Embossing-era
   concepts (plate selection, counter plates/recesses, row indicators) must
   not reappear in code.

License: PolyForm Noncommercial 1.0.0
"""

import re

import pytest

from conftest import SCAD_FILE

NUM_LINES = 20


def strip_comments(scad_source: str) -> str:
    """Remove // line comments and /* */ block comments from OpenSCAD source."""
    no_block = re.sub(r"/\*.*?\*/", "", scad_source, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


@pytest.fixture(scope="module")
def scad_content():
    return SCAD_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def scad_code(scad_content):
    """Source with comments stripped: only real code remains."""
    return strip_comments(scad_content)


class TestTwentyLines:
    def test_all_line_parameters_declared(self, scad_content):
        """Line_1 .. Line_20 must all be declared as top-level parameters."""
        missing = []
        for n in range(1, NUM_LINES + 1):
            if not re.search(rf'^Line_{n}\s*=\s*"', scad_content, flags=re.MULTILINE):
                missing.append(f"Line_{n}")
        assert not missing, f"Missing Line_N parameter declarations: {missing}"

    def test_all_lines_list_contains_every_line(self, scad_code):
        """_all_lines must list Line_1 .. Line_20 (the single source of truth)."""
        match = re.search(r"_all_lines\s*=\s*\[([^\]]+)\]", scad_code)
        assert match, "_all_lines assignment not found"
        listed = [item.strip() for item in match.group(1).split(",")]
        expected = [f"Line_{n}" for n in range(1, NUM_LINES + 1)]
        assert listed == expected, (
            f"_all_lines must be exactly Line_1..Line_{NUM_LINES} in order, got: {listed}"
        )

    def test_no_hardcoded_line_lists_outside_all_lines(self, scad_code):
        """
        Geometry/warning/echo code must iterate _all_lines, not Line_N directly.

        Only the Line_N parameter declarations themselves and the _all_lines
        assignment may reference the Line_N names.
        """
        code = re.sub(r"_all_lines\s*=\s*\[[^\]]+\]", "", scad_code)
        code = re.sub(r'^\s*Line_\d+\s*=\s*"[^"]*"\s*;', "", code, flags=re.MULTILINE)
        stray = sorted(set(re.findall(r"\bLine_\d+\b", code)))
        assert not stray, (
            "Line_N referenced outside its declaration and the _all_lines "
            f"assignment (iterate _all_lines instead): {stray}"
        )

    def test_grid_rows_slider_reaches_20(self, scad_content):
        match = re.search(
            r"^grid_rows\s*=\s*(\d+)\s*;\s*//\s*\[(\d+):(\d+):(\d+)\]",
            scad_content,
            flags=re.MULTILINE,
        )
        assert match, "grid_rows slider declaration not found"
        assert match.group(4) == str(NUM_LINES), (
            f"grid_rows slider max must be {NUM_LINES}, got {match.group(4)}"
        )


class TestWarningsPreviewOnly:
    def test_warning_slot_uses_background_modifier(self, scad_code):
        """
        The shared warning module must render under `%` so warnings are
        preview-only and can never fuse into the exported STL.
        """
        match = re.search(
            r"module\s+warning_slot\s*\([^)]*\)\s*\{(.*?)\n\}", scad_code, flags=re.DOTALL
        )
        assert match, "module warning_slot not found"
        assert "%" in match.group(1), (
            "warning_slot must wrap its geometry in the % background modifier"
        )

    def test_text_only_used_inside_warning_slot(self, scad_code):
        """
        text() must only appear inside warning_slot: any other use risks
        exporting solid text into the STL.
        """
        code_without_slot = re.sub(
            r"module\s+warning_slot\s*\([^)]*\)\s*\{.*?\n\}",
            "",
            scad_code,
            flags=re.DOTALL,
        )
        stray_text_calls = re.findall(r"\btext\s*\(", code_without_slot)
        assert not stray_text_calls, (
            "text() used outside warning_slot; solid text would export into the STL"
        )


class TestMissionGuard:
    """This project is a directly readable card. Embossing concepts stay out."""

    FORBIDDEN_TOKENS = [
        "plate_type",
        "counter_recess",
        "indicator",
        "Embossing",
    ]

    @pytest.mark.parametrize("token", FORBIDDEN_TOKENS)
    def test_forbidden_token_absent_from_code(self, scad_code, token):
        found = re.findall(rf"\b\w*{re.escape(token)}\w*\b", scad_code, flags=re.IGNORECASE)
        assert not found, (
            f"Embossing-era token '{token}' found in code: {sorted(set(found))}. "
            "This generator is a pure directly-readable braille card; plate "
            "selection, counter plates/recesses, and indicators were removed "
            "for the 1.0.0 public release and must not return."
        )

    def test_no_test_system_shims(self, scad_code):
        """The parent repo's hidden test-system parameters must stay removed."""
        for shim in ("combined_shape", "indicator_shapes", "hemisphere_quality"):
            assert shim not in scad_code, (
                f"Parent test-system shim '{shim}' reappeared; the standalone "
                "suite passes real parameter names via -D instead."
            )

    def test_braille_card_is_union_only(self, scad_code):
        """
        braille_card() must not subtract anything: nothing is recessed on a
        pure reading card, and accidental difference() reintroduces the
        coplanar-recess class of non-manifold export bugs.
        """
        match = re.search(
            r"module\s+braille_card\s*\(\s*\)\s*\{(.*?)\n\}", scad_code, flags=re.DOTALL
        )
        assert match, "module braille_card not found"
        assert "difference" not in match.group(1), (
            "braille_card() must be a plain union (nothing is subtracted on a "
            "directly readable card)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
