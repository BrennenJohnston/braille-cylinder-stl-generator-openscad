"""
Parameter Schema Validation

Validates that OpenSCAD Customizer parameters match the web UI schema
according to the parameter mapping definition.

This ensures:
1. All OpenSCAD parameters have web API mappings
2. Default values match across platforms
3. Ranges/enums are consistent
4. Sections/groupings align

License: PolyForm Noncommercial 1.0.0
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


class ParameterSchemaValidator:
    """Validate parameter consistency between OpenSCAD and web API."""

    def __init__(
        self,
        scad_file: Path,
        parameter_mapping_file: Path,
    ):
        """
        Initialize validator.

        Args:
            scad_file: Path to OpenSCAD .scad file
            parameter_mapping_file: Path to parameter_mapping.json
        """
        self.scad_file = scad_file
        self.parameter_mapping_file = parameter_mapping_file

        # Load parameter mapping
        with open(parameter_mapping_file, encoding="utf-8") as f:
            self.mapping_data = json.load(f)

        self.parameters = self.mapping_data["parameters"]
        self.validation_rules = self.mapping_data["validation_rules"]

        # Extract OpenSCAD parameters
        self.openscad_params = self._extract_openscad_parameters()

    def _extract_openscad_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract parameters from OpenSCAD file.

        Parses the .scad file to extract:
        - Parameter names
        - Default values
        - Allowed values (for enums)
        - Comments/descriptions
        - Section headers

        Only extracts user-facing parameters from Customizer sections.
        Stops at /* [Hidden] */ section or when reaching code sections.

        Returns:
            Dictionary of parameter name -> parameter info
        """
        params = {}
        current_section = None

        with open(self.scad_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for section header: /* [Section Name] */
            section_match = re.match(r"/\*\s*\[([^\]]+)\]\s*\*/", line)
            if section_match:
                section_name = section_match.group(1).strip()
                
                # Stop parsing if we hit [Hidden] section or calculated values
                if section_name.lower() == "hidden":
                    break
                
                current_section = section_name
                i += 1
                continue
            
            # Stop if we hit module/function/calculated sections
            if (line.startswith("module ") or 
                line.startswith("function ") or
                "CALCULATED VALUES" in line or
                "Do not modify" in line):
                break

            # Check for parameter definition
            # Format: param_name = value; // comment
            # or: param_name = value; // [option1:Label 1, option2:Label 2]
            param_match = re.match(
                r"^(\w+)\s*=\s*([^;]+);(?:\s*//\s*(.*))?$", line
            )
            if param_match and current_section:
                param_name = param_match.group(1)
                param_value_str = param_match.group(2).strip()
                param_comment = param_match.group(3) or ""

                # Parse default value
                param_value = self._parse_openscad_value(param_value_str)

                # Parse enum values + numeric slider range if present.
                # Customizer comments use two `[...]` forms:
                #   - Dropdown: `// [Option1, Option2]`
                #   - Slider:   `// [min:step:max]`  (e.g. `[0:0.1:5]`)
                # Both share the bracket syntax; we discriminate on whether
                # the contents look like a `min:step:max` numeric triple.
                enum_values = None
                enum_labels = {}
                slider_range = None  # (min, step, max) when present
                enum_match = re.search(
                    r"\[([^\]]+)\]", param_comment
                )
                if enum_match:
                    enum_spec = enum_match.group(1).strip()
                    slider_match = re.match(
                        r"^\s*(-?\d+(?:\.\d+)?)\s*:\s*"
                        r"(-?\d+(?:\.\d+)?)\s*:\s*"
                        r"(-?\d+(?:\.\d+)?)\s*$",
                        enum_spec,
                    )
                    if slider_match:
                        slider_range = (
                            float(slider_match.group(1)),
                            float(slider_match.group(2)),
                            float(slider_match.group(3)),
                        )
                    else:
                        enum_values = []
                        for option in enum_spec.split(","):
                            option = option.strip()
                            if ":" in option:
                                value, label = option.split(":", 1)
                                value = value.strip().strip('"')
                                label = label.strip()
                                enum_values.append(value)
                                enum_labels[value] = label
                            else:
                                value = option.strip().strip('"')
                                enum_values.append(value)

                # Get description (comment without enum spec)
                description = re.sub(r"\[([^\]]+)\]", "", param_comment).strip()

                params[param_name] = {
                    "name": param_name,
                    "default": param_value,
                    "section": current_section,
                    "description": description,
                    "enum_values": enum_values,
                    "enum_labels": enum_labels,
                    "slider_range": slider_range,
                }

            i += 1

        return params

    def _parse_openscad_value(self, value_str: str) -> Any:
        """
        Parse OpenSCAD value string to Python type.

        Args:
            value_str: Value string from OpenSCAD

        Returns:
            Parsed value
        """
        value_str = value_str.strip()

        # String (with quotes)
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # Remove quotes

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Number (int or float)
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Default: return as string
        return value_str

    def validate(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate parameter schema.

        Returns:
            Tuple of (all_passed, list of validation results)
        """
        results = []

        # Run validation checks
        results.extend(self._check_all_mapped())
        results.extend(self._check_defaults_match())
        results.extend(self._check_types_compatible())
        results.extend(self._check_enums_match())
        results.extend(self._check_slider_ranges_match())
        results.extend(self._check_sections_align())

        # Determine overall pass/fail
        errors = [r for r in results if r["severity"] == "error" and not r["passed"]]
        all_passed = len(errors) == 0

        return all_passed, results

    def _check_all_mapped(self) -> List[Dict[str, Any]]:
        """Check that all OpenSCAD parameters have web API mappings."""
        results = []

        # Get mapped OpenSCAD param names
        mapped_openscad_names = {p["openscad_name"] for p in self.parameters}

        # Check each OpenSCAD param
        for param_name in self.openscad_params:
            if param_name not in mapped_openscad_names:
                results.append(
                    {
                        "check": "all_openscad_params_mapped",
                        "severity": "error",
                        "passed": False,
                        "message": f"OpenSCAD parameter '{param_name}' has no web API mapping",
                        "parameter": param_name,
                    }
                )

        # If all mapped, record success
        if not results:
            results.append(
                {
                    "check": "all_openscad_params_mapped",
                    "severity": "error",
                    "passed": True,
                    "message": f"All {len(self.openscad_params)} OpenSCAD parameters are mapped",
                }
            )

        return results

    def _check_defaults_match(self) -> List[Dict[str, Any]]:
        """Check that default values match between OpenSCAD and mapping."""
        results = []

        for param_def in self.parameters:
            openscad_name = param_def["openscad_name"]
            expected_default = param_def["default"]

            if openscad_name not in self.openscad_params:
                continue  # Skip if not in OpenSCAD (will be caught by all_mapped check)

            actual_default = self.openscad_params[openscad_name]["default"]

            # Compare defaults (handle type differences)
            if not self._values_match(expected_default, actual_default):
                results.append(
                    {
                        "check": "default_values_match",
                        "severity": "error",
                        "passed": False,
                        "message": f"Default value mismatch for '{openscad_name}': "
                        f"mapping={expected_default!r}, openscad={actual_default!r}",
                        "parameter": openscad_name,
                        "expected": expected_default,
                        "actual": actual_default,
                    }
                )

        # If all matched, record success
        if not results:
            results.append(
                {
                    "check": "default_values_match",
                    "severity": "error",
                    "passed": True,
                    "message": "All default values match",
                }
            )

        return results

    def _check_types_compatible(self) -> List[Dict[str, Any]]:
        """Check that types are compatible."""
        results = []

        for param_def in self.parameters:
            openscad_name = param_def["openscad_name"]
            expected_type = param_def["type"]

            if openscad_name not in self.openscad_params:
                continue

            actual_value = self.openscad_params[openscad_name]["default"]
            actual_type = type(actual_value).__name__

            # Map Python types to parameter types
            type_mapping = {
                "str": "string",
                "int": "integer",
                "float": "float",
                "bool": "boolean",
            }

            actual_param_type = type_mapping.get(actual_type, actual_type)

            # For enums, check if it's a string with allowed values
            if expected_type == "enum":
                if actual_type != "str":
                    results.append(
                        {
                            "check": "types_compatible",
                            "severity": "error",
                            "passed": False,
                            "message": f"Type mismatch for '{openscad_name}': "
                            f"expected enum (string), got {actual_type}",
                            "parameter": openscad_name,
                        }
                    )
            # Allow integer/float interchangeability (OpenSCAD treats them the same)
            elif expected_type in ["float", "integer"] and actual_param_type in ["float", "integer"]:
                # int and float are compatible for numeric parameters
                pass
            elif expected_type != actual_param_type:
                results.append(
                    {
                        "check": "types_compatible",
                        "severity": "error",
                        "passed": False,
                        "message": f"Type mismatch for '{openscad_name}': "
                        f"expected {expected_type}, got {actual_param_type}",
                        "parameter": openscad_name,
                        "expected_type": expected_type,
                        "actual_type": actual_param_type,
                    }
                )

        # If all matched, record success
        if not results:
            results.append(
                {
                    "check": "types_compatible",
                    "severity": "error",
                    "passed": True,
                    "message": "All types are compatible",
                }
            )

        return results

    def _check_enums_match(self) -> List[Dict[str, Any]]:
        """Check that enum values match."""
        results = []

        for param_def in self.parameters:
            if param_def["type"] != "enum":
                continue

            openscad_name = param_def["openscad_name"]
            expected_values = set(param_def["values"])

            if openscad_name not in self.openscad_params:
                continue

            openscad_param = self.openscad_params[openscad_name]
            actual_values = set(openscad_param.get("enum_values") or [])

            if expected_values != actual_values:
                results.append(
                    {
                        "check": "enums_match",
                        "severity": "warning",
                        "passed": False,
                        "message": f"Enum values mismatch for '{openscad_name}': "
                        f"mapping={sorted(expected_values)}, "
                        f"openscad={sorted(actual_values)}",
                        "parameter": openscad_name,
                        "expected_values": sorted(expected_values),
                        "actual_values": sorted(actual_values),
                    }
                )

        return results

    def _check_slider_ranges_match(self) -> List[Dict[str, Any]]:
        """
        Check that OpenSCAD `// [min:step:max]` slider ranges agree with the
        ``range`` field in parameter_mapping.json. Only applies to numeric
        parameters that declare both a slider range in the SCAD comment and
        a ``range`` entry in the mapping. Mismatches are reported as
        errors so a divergent slider can't ship unnoticed.
        """
        results = []
        checked = 0

        for param_def in self.parameters:
            mapping_range = param_def.get("range")
            if not mapping_range:
                continue  # Mapping has no range -> nothing to compare.

            openscad_name = param_def["openscad_name"]
            openscad_param = self.openscad_params.get(openscad_name)
            if openscad_param is None:
                continue  # Caught by the all_mapped check.

            slider_range = openscad_param.get("slider_range")
            if slider_range is None:
                continue  # SCAD declaration is not a numeric slider.

            checked += 1
            scad_min, _step, scad_max = slider_range
            try:
                expected_min, expected_max = float(mapping_range[0]), float(
                    mapping_range[1]
                )
            except (TypeError, ValueError, IndexError):
                results.append(
                    {
                        "check": "slider_ranges_match",
                        "severity": "error",
                        "passed": False,
                        "message": (
                            f"`range` field for '{openscad_name}' in "
                            f"parameter_mapping.json is malformed: "
                            f"{mapping_range!r}; expected [min, max]."
                        ),
                        "parameter": openscad_name,
                    }
                )
                continue

            if abs(scad_min - expected_min) > 1e-9 or abs(scad_max - expected_max) > 1e-9:
                results.append(
                    {
                        "check": "slider_ranges_match",
                        "severity": "error",
                        "passed": False,
                        "message": (
                            f"Slider range mismatch for '{openscad_name}': "
                            f"openscad=[{scad_min}, {scad_max}], "
                            f"mapping=[{expected_min}, {expected_max}]. "
                            f"Update either the OpenSCAD `[min:step:max]` "
                            f"comment or the parameter_mapping.json `range` "
                            f"entry so they agree."
                        ),
                        "parameter": openscad_name,
                        "scad_range": [scad_min, scad_max],
                        "mapping_range": [expected_min, expected_max],
                    }
                )

        if checked == 0:
            results.append(
                {
                    "check": "slider_ranges_match",
                    "severity": "info",
                    "passed": True,
                    "message": (
                        "Slider-range check skipped: no parameters had both "
                        "a SCAD `[min:step:max]` comment and a mapping "
                        "`range` entry."
                    ),
                }
            )
        elif not any(
            r["check"] == "slider_ranges_match" and not r["passed"]
            for r in results
        ):
            results.append(
                {
                    "check": "slider_ranges_match",
                    "severity": "error",
                    "passed": True,
                    "message": (
                        f"All {checked} OpenSCAD slider ranges match "
                        f"parameter_mapping.json"
                    ),
                }
            )

        return results

    def _check_sections_align(self) -> List[Dict[str, Any]]:
        """Check that section/grouping labels align."""
        results = []

        for param_def in self.parameters:
            openscad_name = param_def["openscad_name"]
            expected_section = param_def.get("section")

            if openscad_name not in self.openscad_params:
                continue

            actual_section = self.openscad_params[openscad_name].get("section")

            # Sections don't need to match exactly (different organizations are OK)
            # but we log mismatches as warnings
            if expected_section and actual_section:
                if expected_section != actual_section:
                    results.append(
                        {
                            "check": "sections_align",
                            "severity": "info",
                            "passed": False,
                            "message": f"Section mismatch for '{openscad_name}': "
                            f"mapping='{expected_section}', "
                            f"openscad='{actual_section}'",
                            "parameter": openscad_name,
                        }
                    )

        return results

    def _values_match(self, expected: Any, actual: Any) -> bool:
        """Check if two values match (with type flexibility)."""
        # Handle float/int equivalence
        if isinstance(expected, (int, float)) and isinstance(
            actual, (int, float)
        ):
            return abs(expected - actual) < 1e-9

        # Handle string comparison
        if isinstance(expected, str) and isinstance(actual, str):
            return expected == actual

        # Handle boolean
        if isinstance(expected, bool) and isinstance(actual, bool):
            return expected == actual

        # Default equality
        return expected == actual


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate parameter schema consistency"
    )
    parser.add_argument(
        "--scad-file",
        type=Path,
        default=PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad",
        help="OpenSCAD file to validate",
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=PROJECT_ROOT / "tests" / "parameter_mapping.json",
        help="Parameter mapping JSON file",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Output validation results as JSON",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        # Create validator
        validator = ParameterSchemaValidator(
            scad_file=args.scad_file,
            parameter_mapping_file=args.mapping_file,
        )

        logger.info(f"Validating: {args.scad_file.name}")
        logger.info(
            f"Found {len(validator.openscad_params)} OpenSCAD parameters"
        )

        # Run validation
        all_passed, results = validator.validate()

        # Print results
        print("\n" + "=" * 70)
        print("PARAMETER SCHEMA VALIDATION RESULTS")
        print("=" * 70)

        # Group by severity. Info-level results are counted in the summary
        # below but never listed individually, so they are not collected here.
        errors = [r for r in results if r["severity"] == "error"]
        warnings = [r for r in results if r["severity"] == "warning"]

        # Print errors
        failed_errors = [e for e in errors if not e["passed"]]
        if failed_errors:
            print("\n✗ ERRORS:")
            for result in failed_errors:
                print(f"  - {result['message']}")

        # Print warnings
        failed_warnings = [w for w in warnings if not w["passed"]]
        if failed_warnings:
            print("\n⚠ WARNINGS:")
            for result in failed_warnings:
                print(f"  - {result['message']}")

        # Print passed checks
        passed_checks = [r for r in errors if r["passed"]]
        if passed_checks:
            print("\n✓ PASSED:")
            for result in passed_checks:
                print(f"  - {result['message']}")

        # Summary
        print("\n" + "=" * 70)
        if all_passed:
            print("✓ ALL VALIDATION CHECKS PASSED")
        else:
            print(f"✗ VALIDATION FAILED ({len(failed_errors)} error(s))")
        print("=" * 70)

        # Save JSON output if requested
        if args.output_json:
            output_data = {
                "passed": all_passed,
                "total_checks": len(results),
                "errors": len(failed_errors),
                "warnings": len(failed_warnings),
                "results": results,
            }
            with open(args.output_json, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Results saved to: {args.output_json}")

        return 0 if all_passed else 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
