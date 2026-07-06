"""
Guard that the MakerWorld single-file build stays in sync with the canonical
dual-file desktop generator.

MakerWorld's Parametric Model Maker accepts only one .scad file and does not
support `include <...>`, so `makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad`
is a flattened copy of the canonical main file with presets.scad inlined and
`dot_shape` defaulting to "Cone".

These tests prevent geometry drift between the two files: the geometry body (from
the BACKWARD COMPATIBILITY marker to EOF) must be byte-identical to the canonical
main file. See makerworld/README.md for the maintainer re-flatten procedure.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "Braille_Cylinder_STL_Generator.scad"
MAKERWORLD = REPO_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld.scad"

# The geometry body starts at this marker and runs to EOF. Everything below it
# must be identical between the canonical file and the MakerWorld flattened copy.
BODY_MARKER = "// BACKWARD COMPATIBILITY - Test System Parameters"


def _body_from_marker(text: str) -> str:
    idx = text.index(BODY_MARKER)
    return text[idx:]


def test_makerworld_file_exists():
    assert MAKERWORLD.exists(), f"Missing MakerWorld single-file build: {MAKERWORLD}"


def test_geometry_body_is_byte_identical():
    """The geometry body (marker -> EOF) must match the canonical main file."""
    canonical = CANONICAL.read_text(encoding="utf-8")
    makerworld = MAKERWORLD.read_text(encoding="utf-8")

    assert BODY_MARKER in canonical, "BACKWARD COMPATIBILITY marker missing from canonical file"
    assert BODY_MARKER in makerworld, "BACKWARD COMPATIBILITY marker missing from MakerWorld file"

    canonical_body = _body_from_marker(canonical)
    makerworld_body = _body_from_marker(makerworld)

    assert makerworld_body == canonical_body, (
        "MakerWorld geometry body has drifted from the canonical main file. "
        "Re-flatten per makerworld/README.md (copy the canonical file from the "
        "BACKWARD COMPATIBILITY marker to EOF over the MakerWorld file's body)."
    )


def test_indicator_fix_present_in_body():
    """The mirrored-pair indicator fix lives in the shared geometry body, so it
    must be carried into the MakerWorld build too."""
    makerworld = MAKERWORLD.read_text(encoding="utf-8")
    assert "module place_row_indicators" in makerworld
    assert "mirror([0, 1, 0])" in makerworld


def test_presets_are_inlined_with_sentinels():
    """presets.scad must be inlined (no include) between BEGIN/END sentinels."""
    makerworld = MAKERWORLD.read_text(encoding="utf-8")

    # Forbid an ACTIVE include directive (line-anchored), not prose mentions of
    # it inside the explanatory header comments.
    assert "\ninclude <presets.scad>" not in makerworld, (
        "MakerWorld file must not use an active include <presets.scad>; directive; "
        "MakerWorld rejects local includes."
    )
    assert "// ==== BEGIN inlined from presets.scad" in makerworld
    assert "// ==== END inlined from presets.scad ====" in makerworld

    # The inlined region must actually contain the preset tables + helpers.
    assert "PRESET_04 = [" in makerworld
    assert "PRESET_03 = [" in makerworld
    assert "function preset_value(" in makerworld


def test_dot_shape_defaults_to_cone():
    """Both builds ship with the Cone default (dropdown still offers Rounded)."""
    makerworld = MAKERWORLD.read_text(encoding="utf-8")
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert 'dot_shape = "Cone"; // [Rounded, Cone]' in makerworld
    assert 'dot_shape = "Cone"; // [Rounded, Cone]' in canonical
