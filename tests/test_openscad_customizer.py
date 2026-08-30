"""
OpenSCAD Customizer Validation Tests

Verifies that OpenSCAD Customizer dropdown definitions are correct and won't
cause duplicate option issues in the UI.

This test was added after discovering that the `value:Label` format can cause
duplicate dropdown entries in some OpenSCAD versions. The recommended format is:
  param = "DefaultLabel"; // [Label1, Label2, Label3]

Where the default value exactly matches one of the dropdown options.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"


class TestOpenSCADCustomizer:
    """Test OpenSCAD Customizer dropdown definitions."""

    @pytest.fixture
    def scad_content(self):
        """Load the OpenSCAD file content."""
        return SCAD_FILE.read_text(encoding="utf-8")

    def test_scad_file_exists(self):
        """Verify the OpenSCAD file exists."""
        assert SCAD_FILE.exists(), f"OpenSCAD file not found: {SCAD_FILE}"

    def test_no_value_colon_label_format(self, scad_content):
        """
        Check that dropdowns don't use the problematic 'value:Label' format.

        The format `// [value1:Label1, value2:Label2]` can cause duplicate entries
        in the OpenSCAD Customizer. The preferred format is:
        `// [Label1, Label2]` where the default value is one of the labels.

        Note: This does NOT apply to range sliders which use `// [min:step:max]`.
        """
        dropdown_lines_with_colon = []
        for line in scad_content.split("\n"):
            # Skip lines that don't have assignments or start with //
            if "=" not in line or line.strip().startswith("//"):
                continue

            # Look for comment with brackets
            bracket_match = re.search(r"//\s*\[([^\]]+)\]", line)
            if not bracket_match:
                continue

            bracket_content = bracket_match.group(1)

            # Skip range sliders: they contain only numbers, colons, and periods
            # E.g., "10:0.1:100" or "-10:0.1:10" or "1:1:20"
            if re.match(r"^-?[\d.]+:-?[\d.]+:-?[\d.]+$", bracket_content.strip()):
                continue

            # Check if this looks like a dropdown with value:Label format
            # Look for patterns like "value:Label" with word characters
            # But not patterns that are just numbers (ranges)
            if re.search(r"[a-zA-Z]\w*:[A-Z]", bracket_content):
                dropdown_lines_with_colon.append(line.strip())

        if dropdown_lines_with_colon:
            pytest.fail(
                "Found dropdown definitions using problematic 'value:Label' format.\n"
                "This format can cause duplicate entries in OpenSCAD Customizer.\n"
                "Problematic lines:\n"
                + "\n".join(f"  - {line}" for line in dropdown_lines_with_colon)
                + '\n\nRecommended format: param = "DefaultLabel"; // [Label1, Label2]'
            )

    def test_dropdown_default_matches_option(self, scad_content):
        """
        Verify that dropdown default values match one of the options exactly.

        If the default doesn't match an option exactly, OpenSCAD may show
        both the default and the closest option as separate entries.
        """
        # Pattern to find dropdown definitions
        # Matches: variable = "default"; // [option1, option2, ...]
        dropdown_pattern = r'(\w+)\s*=\s*"([^"]+)"\s*;\s*//\s*\[([^\]]+)\]'

        mismatches = []
        for match in re.finditer(dropdown_pattern, scad_content):
            var_name = match.group(1)
            default_value = match.group(2)
            options_str = match.group(3)

            # Parse options (split by comma, strip whitespace)
            options = [opt.strip() for opt in options_str.split(",")]

            # Check if default matches one of the options
            if default_value not in options:
                mismatches.append(
                    {"variable": var_name, "default": default_value, "options": options}
                )

        if mismatches:
            msg = "Dropdown default values don't match any option:\n"
            for m in mismatches:
                msg += f"  - {m['variable']}: default '{m['default']}' not in {m['options']}\n"
            msg += "\nThis can cause duplicate entries in OpenSCAD Customizer."
            pytest.fail(msg)

    def test_no_duplicate_dropdown_options(self, scad_content):
        """Check that dropdown options don't contain duplicates."""
        dropdown_pattern = r'(\w+)\s*=\s*"[^"]+"\s*;\s*//\s*\[([^\]]+)\]'

        duplicates = []
        for match in re.finditer(dropdown_pattern, scad_content):
            var_name = match.group(1)
            options_str = match.group(2)

            options = [opt.strip() for opt in options_str.split(",")]
            seen = set()
            for opt in options:
                if opt in seen:
                    duplicates.append({"variable": var_name, "duplicate": opt})
                seen.add(opt)

        if duplicates:
            msg = "Dropdown definitions contain duplicate options:\n"
            for d in duplicates:
                msg += f"  - {d['variable']}: duplicate option '{d['duplicate']}'\n"
            pytest.fail(msg)

    def test_card_support_removed(self, scad_content):
        """Verify that card support has been completely removed."""
        # Check that there are no card-related modules
        card_modules = ["card_emboss_plate", "card_counter_plate"]
        found_modules = []

        for module in card_modules:
            if f"module {module}" in scad_content:
                found_modules.append(module)

        if found_modules:
            pytest.fail(
                f"Card support should be removed but found modules: {found_modules}\n"
                "Card support was permanently removed in favor of cylinder-only operation."
            )

    def test_shape_type_not_in_ui(self, scad_content):
        """Verify shape_type is not exposed in UI (cylinder-only)."""
        # Check that shape_type is not a visible dropdown parameter
        # It should only be in Hidden section for backward compatibility

        # Find the line with shape_type definition
        shape_type_pattern = r'shape_type\s*=\s*"[^"]*"\s*;'

        for line in scad_content.split("\n"):
            if re.search(shape_type_pattern, line):
                # If it has a dropdown comment, it's visible in UI (bad)
                if re.search(r"//\s*\[", line) and "card" in line.lower():
                    pytest.fail(
                        "shape_type should not offer card option in UI.\n"
                        f"Found: {line.strip()}"
                    )


class TestBackwardCompatibility:
    """Test backward compatibility with test system parameters."""

    @pytest.fixture
    def scad_content(self):
        """Load the OpenSCAD file content."""
        return SCAD_FILE.read_text(encoding="utf-8")

    def test_test_system_parameters_exist(self, scad_content):
        """Verify hidden parameters for test system compatibility exist."""
        required_params = [
            "combined_shape",  # Test system param for dot shape
            "indicator_shapes",  # Test system param for indicators
            "hemisphere_quality",  # Test system param for render quality
        ]

        missing = []
        for param in required_params:
            # Check for hidden parameter definition
            if f'{param} = ""' not in scad_content:
                missing.append(param)

        if missing:
            pytest.fail(
                f"Missing backward compatibility parameters: {missing}\n"
                "These hidden parameters are required for the test system to work."
            )

    def test_normalization_handles_both_formats(self, scad_content):
        """Verify normalization code handles both UI labels and test values."""
        # Check for key normalization patterns
        patterns_to_find = [
            r'plate_type\s*==\s*"positive"',  # Test system value
            r'plate_type\s*==\s*"Embossing Plate"',  # UI value
            r'combined_shape\s*==\s*"rounded"',  # Test system value
            r'dot_shape\s*==\s*"Rounded"',  # UI value
            r'indicator_shapes\s*==\s*"on"',  # Test system value
            r'indicators\s*==\s*"On"',  # UI value
        ]

        missing_patterns = []
        for pattern in patterns_to_find:
            if not re.search(pattern, scad_content):
                missing_patterns.append(pattern)

        if missing_patterns:
            pytest.fail(
                "Normalization code missing handling for patterns:\n"
                + "\n".join(f"  - {p}" for p in missing_patterns)
                + "\n\nBoth UI labels and test system values must be normalized."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
