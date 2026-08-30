"""
Backward-Compatibility Parameter Placement Tests

The OpenSCAD test runner drives the SCAD via -D flags using legacy parameter
names (``combined_shape``, ``indicator_shapes``, ``hemisphere_quality``,
``shape_type``). Those variables must still exist in the .scad file but must
NOT appear in the Customizer UI — otherwise OpenSCAD renders them as
duplicate / orphan controls alongside the canonical ``dot_shape`` /
``indicators`` / ``render_quality`` parameters.

Phase 5 pinned the four backward-compat declarations under a dedicated
``/* [Hidden] */`` marker. This file regression-tests that placement so a
future refactor can't accidentally hoist them out of the hidden block.

The check is intentionally robust against line-number shifts: we walk every
section marker (``/* [Name] */``) in source order and verify the *current*
section at the point each backward-compat variable is declared is
``Hidden``. We never hardcode line numbers.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

# Names of the four legacy parameters that the test runner passes via -D.
# Each must be declared inside a `/* [Hidden] */` block.
BACKWARD_COMPAT_VARS = (
    "combined_shape",
    "indicator_shapes",
    "hemisphere_quality",
    "shape_type",
)

# Regex for a Customizer section marker: `/* [Section Name] */`.
# Matches anywhere on a stripped line; the captured group is the section name.
_SECTION_RE = re.compile(r"^\s*/\*\s*\[([^\]]+)\]\s*\*/\s*$")


def _read_scad_lines():
    """Read the SCAD file as a list of CR-stripped logical lines."""
    text = SCAD_FILE.read_text(encoding="utf-8")
    # CRLF on Windows checkouts shouldn't break the section regex.
    return text.replace("\r\n", "\n").split("\n")


def _find_declaration_section(lines, var_name):
    """
    Walk `lines` top-down and return the Customizer section name in effect
    when the first `var_name = ...;` declaration is encountered.

    Returns None if no declaration is found.
    """
    decl_re = re.compile(rf"^\s*{re.escape(var_name)}\s*=")
    current_section = None
    for line in lines:
        m = _SECTION_RE.match(line)
        if m:
            current_section = m.group(1).strip()
            continue
        if decl_re.match(line):
            return current_section
    return None


class TestBackwardCompatHidden:
    """Verify each legacy test-system parameter is inside /* [Hidden] */."""

    @pytest.fixture(scope="class")
    def scad_lines(self):
        assert SCAD_FILE.exists(), f"SCAD file missing: {SCAD_FILE}"
        return _read_scad_lines()

    @pytest.mark.parametrize("var_name", BACKWARD_COMPAT_VARS)
    def test_var_inside_hidden_section(self, scad_lines, var_name):
        """The most recent /* [Section] */ before the declaration must be Hidden."""
        section = _find_declaration_section(scad_lines, var_name)
        assert section is not None, (
            f"Backward-compat variable `{var_name}` is not declared anywhere "
            f"in {SCAD_FILE.name}. The test runner depends on it; restore the "
            f"declaration inside the /* [Hidden] */ block."
        )
        assert section.lower() == "hidden", (
            f"Backward-compat variable `{var_name}` is declared under "
            f"`/* [{section}] */` instead of `/* [Hidden] */`. Move it back "
            f"into the hidden block so OpenSCAD's Customizer doesn't render "
            f"it as an orphan UI control."
        )

    def test_all_compat_vars_declared(self, scad_lines):
        """Sanity check: each backward-compat var has exactly one declaration."""
        for var_name in BACKWARD_COMPAT_VARS:
            decl_re = re.compile(rf"^\s*{re.escape(var_name)}\s*=", re.MULTILINE)
            joined = "\n".join(scad_lines)
            matches = decl_re.findall(joined)
            assert len(matches) == 1, (
                f"Expected exactly one declaration of `{var_name}` in "
                f"{SCAD_FILE.name}, found {len(matches)}."
            )

    def test_hidden_block_uses_empty_string_default(self, scad_lines):
        """
        Each backward-compat var should default to an empty string so the
        normalization expressions in the calculated-values section know to
        fall back to the human-facing UI parameter.
        """
        joined = "\n".join(scad_lines)
        for var_name in BACKWARD_COMPAT_VARS:
            decl_re = re.compile(rf'^\s*{re.escape(var_name)}\s*=\s*"";', re.MULTILINE)
            assert decl_re.search(joined), (
                f"Backward-compat variable `{var_name}` must default to "
                f'`""` (empty string). Anything else would short-circuit '
                f"the normalization fallback for the canonical UI parameter."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
