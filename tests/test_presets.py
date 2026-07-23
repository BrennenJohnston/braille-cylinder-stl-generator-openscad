"""
Paper-Thickness Preset Tests

Verifies the data-driven preset system extracted from the main SCAD file in
Phase 5c. The preset tables live in ``presets.scad`` (PRESET_04 / PRESET_03)
and are routed through ``preset_value(preset, key, fallback)``. The main
SCAD file consumes them with one ``_preset_<name>`` per parameter.

The contract under test:

1. ``PRESET_04`` and ``PRESET_03`` each contain the same set of
   `[key, value]` rows (21 rows as of this commit) and cover every
   preset-driven parameter consumed by the main file.
   ``grid_columns`` and ``grid_rows`` are deliberately absent: the
   sliders always govern text capacity (matching the web app, where
   thickness presets never override the columns/rows dials).
2. Known numeric values match the documented preset table (mirrors the web
   app's ``THICKNESS_PRESETS`` block in ``public/index.html``).
3. ``preset_value("0.4mm", k, fallback)`` returns the PRESET_04 value;
   ``preset_value("0.3mm", k, fallback)`` returns the PRESET_03 value;
   ``preset_value("Custom", k, fallback)`` (or any unrecognized name) must
   return ``fallback``. The latter is the "Custom preserves slider values"
   contract.
4. The main SCAD wires every preset-driven slider through ``preset_value``
   exactly once, with the slider as the fallback argument.

All assertions parse source files; no OpenSCAD render is required.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
PRESETS_FILE = PROJECT_ROOT / "presets.scad"

# Mirrors PRESET_04 in presets.scad. Order doesn't matter for the equality
# check; values are the source of truth for the customizer behaviour.
# grid_columns/grid_rows are intentionally NOT preset-driven (sliders govern
# text capacity), so they must not appear here or in the tables.
EXPECTED_PRESET_04 = {
    # Spacing
    "cell_spacing": 6.5,
    "line_spacing": 10.0,
    "dot_spacing": 2.5,
    "braille_y_adjust": 0.0,
    # Emboss Rounded
    "rounded_dot_base_diameter": 1.5,
    "rounded_dot_base_height": 0.5,
    "rounded_dot_dome_diameter": 1.0,
    "rounded_dot_dome_height": 0.5,
    # Emboss Cone
    "emboss_dot_base_diameter": 1.5,
    "emboss_dot_height": 0.8,
    "emboss_dot_flat_hat": 0.4,
    # Counter Bowl
    "bowl_counter_dot_base_diameter": 1.8,
    "counter_dot_depth": 0.8,
    # Counter Cone
    "cone_counter_dot_base_diameter": 1.9,
    "cone_counter_dot_height": 0.7,
    "cone_counter_dot_flat_hat": 1.0,
    # Cylinder
    "cylinder_diameter_mm": 30.8,
    "cylinder_height_mm": 52,
    "polygon_cutout_radius_mm": 13,
    "polygon_cutout_points": 12,
    "seam_offset_degrees": 0.0,
}

# Mirrors PRESET_03 in presets.scad (smaller dots / thinner paper). Cylinder
# and spacing rows are identical to PRESET_04 by design.
EXPECTED_PRESET_03 = {
    # Spacing (same as 0.4mm)
    "cell_spacing": 6.5,
    "line_spacing": 10.0,
    "dot_spacing": 2.5,
    "braille_y_adjust": 0.0,
    # Emboss Rounded (smaller)
    "rounded_dot_base_diameter": 1.2,
    "rounded_dot_base_height": 0.4,
    "rounded_dot_dome_diameter": 0.8,
    "rounded_dot_dome_height": 0.4,
    # Emboss Cone (smaller)
    "emboss_dot_base_diameter": 1.2,
    "emboss_dot_height": 0.6,
    "emboss_dot_flat_hat": 0.2,
    # Counter Bowl (smaller)
    "bowl_counter_dot_base_diameter": 1.5,
    "counter_dot_depth": 0.5,
    # Counter Cone (smaller)
    "cone_counter_dot_base_diameter": 1.5,
    "cone_counter_dot_height": 0.5,
    "cone_counter_dot_flat_hat": 0.8,
    # Cylinder (same as 0.4mm)
    "cylinder_diameter_mm": 30.8,
    "cylinder_height_mm": 52,
    "polygon_cutout_radius_mm": 13,
    "polygon_cutout_points": 12,
    "seam_offset_degrees": 0.0,
}


def _parse_preset_table(presets_source, table_name):
    """
    Extract a `[key, value]` lookup table from `presets.scad`.

    Returns a dict mapping key -> Python int/float.

    The presets.scad table syntax is::

        PRESET_04 = [
            ["grid_columns", 11],
            ["cell_spacing", 6.5],
            ...
        ];

    We allow arbitrary whitespace (including comment lines between rows)
    and tolerate a trailing comma after the last entry.
    """
    # Capture everything between `<table_name> = [` and the matching `];`
    block_re = re.compile(
        rf"{re.escape(table_name)}\s*=\s*\[(.*?)\]\s*;",
        re.DOTALL,
    )
    block_match = block_re.search(presets_source)
    assert block_match, (
        f"Could not locate `{table_name}` table in presets.scad. The preset "
        f"system depends on this declaration; restore it before proceeding."
    )
    body = block_match.group(1)

    row_re = re.compile(r'\[\s*"([^"]+)"\s*,\s*([-+0-9.eE]+)\s*\]')
    out = {}
    for key, raw_value in row_re.findall(body):
        if "." in raw_value or "e" in raw_value or "E" in raw_value:
            out[key] = float(raw_value)
        else:
            out[key] = int(raw_value)
    return out


def _values_equal(a, b):
    """Numeric equality with float tolerance, type-agnostic int/float."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return a == b


class TestPresetTables:
    """The two preset lookup tables in presets.scad."""

    @pytest.fixture(scope="class")
    def presets_source(self):
        assert PRESETS_FILE.exists(), f"presets.scad missing: {PRESETS_FILE}"
        return PRESETS_FILE.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def preset_04(self, presets_source):
        return _parse_preset_table(presets_source, "PRESET_04")

    @pytest.fixture(scope="class")
    def preset_03(self, presets_source):
        return _parse_preset_table(presets_source, "PRESET_03")

    def test_preset_04_has_all_expected_keys(self, preset_04):
        missing = set(EXPECTED_PRESET_04) - set(preset_04)
        extra = set(preset_04) - set(EXPECTED_PRESET_04)
        assert not missing, f"PRESET_04 missing keys: {sorted(missing)}"
        assert not extra, (
            f"PRESET_04 has unexpected extra keys: {sorted(extra)}. "
            f"If you intentionally added a parameter to the preset table, "
            f"add it to EXPECTED_PRESET_04 in this test."
        )

    def test_preset_03_has_all_expected_keys(self, preset_03):
        missing = set(EXPECTED_PRESET_03) - set(preset_03)
        extra = set(preset_03) - set(EXPECTED_PRESET_03)
        assert not missing, f"PRESET_03 missing keys: {sorted(missing)}"
        assert not extra, (
            f"PRESET_03 has unexpected extra keys: {sorted(extra)}. "
            f"If you intentionally added a parameter to the preset table, "
            f"add it to EXPECTED_PRESET_03 in this test."
        )

    def test_preset_04_values_match_expected(self, preset_04):
        mismatches = []
        for k, expected in EXPECTED_PRESET_04.items():
            actual = preset_04.get(k)
            if not _values_equal(expected, actual):
                mismatches.append((k, expected, actual))
        assert not mismatches, "PRESET_04 value mismatches:\n" + "\n".join(
            f"  {k}: expected {e!r}, got {a!r}" for k, e, a in mismatches
        )

    def test_preset_03_values_match_expected(self, preset_03):
        mismatches = []
        for k, expected in EXPECTED_PRESET_03.items():
            actual = preset_03.get(k)
            if not _values_equal(expected, actual):
                mismatches.append((k, expected, actual))
        assert not mismatches, "PRESET_03 value mismatches:\n" + "\n".join(
            f"  {k}: expected {e!r}, got {a!r}" for k, e, a in mismatches
        )

    def test_preset_tables_share_same_parameters(self, preset_04, preset_03):
        """Both tables cover the same 21 parameters (just at different sizes)."""
        assert set(preset_04) == set(preset_03), (
            "PRESET_04 and PRESET_03 must cover the same parameters; the "
            "main SCAD looks up the same keys in both."
        )
        assert len(preset_04) == len(EXPECTED_PRESET_04), (
            f"Expected {len(EXPECTED_PRESET_04)} preset rows, got "
            f"{len(preset_04)}. Update EXPECTED_PRESET_04 if the preset "
            f"surface area legitimately changed."
        )


class TestPresetValueHelper:
    """The preset_value() routing function in presets.scad."""

    @pytest.fixture(scope="class")
    def presets_source(self):
        return PRESETS_FILE.read_text(encoding="utf-8")

    def test_helper_routes_04mm_to_preset_04(self, presets_source):
        # The helper body explicitly branches on the literal preset name and
        # delegates to preset_lookup() against PRESET_04.
        assert re.search(
            r'preset\s*==\s*"0\.4mm"\s*\?\s*preset_lookup\(\s*PRESET_04',
            presets_source,
        ), "preset_value() does not route preset=='0.4mm' to PRESET_04"

    def test_helper_routes_03mm_to_preset_03(self, presets_source):
        assert re.search(
            r'preset\s*==\s*"0\.3mm"\s*\?\s*preset_lookup\(\s*PRESET_03',
            presets_source,
        ), "preset_value() does not route preset=='0.3mm' to PRESET_03"

    def test_helper_falls_back_for_custom(self, presets_source):
        """
        For any preset name other than the two recognised ones, the helper
        must return the `fallback` argument so "Custom" preserves the user's
        slider values.
        """
        # The helper's terminator: `val == undef ? fallback : val`.
        assert re.search(
            r"val\s*==\s*undef\s*\?\s*fallback\s*:\s*val", presets_source
        ), (
            "preset_value() must return its `fallback` argument when the "
            "table lookup misses (i.e. for 'Custom' or unrecognized presets). "
            "Restore the `val == undef ? fallback : val` terminator."
        )

        # And the routing branch defaults to `undef` for unknown names so the
        # terminator kicks in. This catches a future refactor that hardcodes
        # PRESET_04 as the default.
        assert re.search(
            r'preset\s*==\s*"0\.3mm"\s*\?\s*preset_lookup\(\s*PRESET_03[^)]*\)\s*:\s*undef',
            presets_source,
        ), (
            "preset_value()'s routing branch must terminate with `: undef` "
            "for unknown preset names; otherwise 'Custom' would silently "
            "inherit one of the preset tables."
        )


class TestMainScadWiring:
    """The main SCAD wires every slider through preset_value()."""

    @pytest.fixture(scope="class")
    def scad_source(self):
        return SCAD_FILE.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def preset_04(self):
        return _parse_preset_table(
            PRESETS_FILE.read_text(encoding="utf-8"), "PRESET_04"
        )

    def test_every_preset_key_wired_through_preset_value(
        self, scad_source, preset_04
    ):
        """
        For every key in PRESET_04 there must be a matching
        `_preset_<key> = preset_value(paper_thickness_preset, "<key>", <key>)`
        line in the main SCAD. The slider name (third arg) must match the
        lookup key — otherwise Custom mode would silently swap parameters.
        """
        wire_re = re.compile(
            r"_preset_(\w+)\s*=\s*preset_value\(\s*"
            r"paper_thickness_preset\s*,\s*"
            r'"(\w+)"\s*,\s*'
            r"(\w+)\s*\)"
        )
        wired = {}
        for varname, key, slider in wire_re.findall(scad_source):
            wired[key] = (varname, slider)

        missing = [k for k in preset_04 if k not in wired]
        assert not missing, (
            "Preset keys are present in presets.scad but not consumed by "
            "the main SCAD via `preset_value(paper_thickness_preset, \"<key>\", <key>)`:\n"
            + "\n".join(f"  - {k}" for k in missing)
        )

        # Slider-name (3rd arg = fallback) must match the lookup key, so
        # Custom mode keeps each slider tied to its own variable.
        mismatched = [
            (k, slider) for k, (_, slider) in wired.items() if slider != k
        ]
        assert not mismatched, (
            "preset_value() fallback (3rd arg) must equal the lookup key "
            "for every parameter, so the Custom preset preserves the "
            "user's slider value. Mismatches:\n"
            + "\n".join(f"  - {k}: fallback is `{s}`" for k, s in mismatched)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
