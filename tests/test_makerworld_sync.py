"""
Guard that the MakerWorld single-file build stays in sync with the canonical
dual-file desktop generator.

MakerWorld's Parametric Model Maker accepts only one .scad file and does not
support `include <...>`, so `makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad`
is a flattened copy of the canonical main file with presets.scad inlined and
`dot_shape` defaulting to "Rounded".

These tests prevent geometry drift between the two files, in three layers:

1. The geometry body (from the BACKWARD COMPATIBILITY marker to EOF) must be
   byte-identical to the canonical main file.
2. Every parameter DECLARATION above that marker - Customizer defaults, slider
   ranges, and the DOUBLE-SIDED (INTERPOINT) MATH constants - must match too.
   Layer 1 alone is blind to defaults, because every declaration sits above the
   marker: that blindness is how `tactile_indicator_length` sat at 5.0 mm in
   this build and 10.0 mm in the canonical one until Phase 08 went looking
   (research memory 2026-08-18). Comments may still differ - this build carries
   its own maintainer prose - but no value or range may.
3. The inlined presets must match presets.scad, which is where the paper
   thickness presets override those defaults.

See makerworld/README.md for the maintainer re-flatten procedure.
"""

import difflib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "Braille_Cylinder_STL_Generator.scad"
MAKERWORLD = REPO_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad"
PRESETS = REPO_ROOT / "presets.scad"

# The geometry body starts at this marker and runs to EOF. Everything below it
# must be identical between the canonical file and the MakerWorld flattened copy.
BODY_MARKER = "// BACKWARD COMPATIBILITY - Test System Parameters"

# presets.scad is pasted between these sentinels in the flattened build.
INLINE_BEGIN = "// ==== BEGIN inlined from presets.scad (MakerWorld single-file requirement) ====\n"
INLINE_END = "// ==== END inlined from presets.scad ===="

# What gets inlined is presets.scad from its own `/* [Hidden] */` marker down;
# the lines above that are the file's own header prose, which has no meaning
# once the content is pasted into the middle of another file. Line-anchored,
# because that prose quotes the marker inline while explaining why it is there.
PRESET_BODY_MARKER = re.compile(r"^/\* \[Hidden\] \*/$", re.MULTILINE)

# A top-level assignment: a name in column 0 followed by `=`. Indented lines are
# skipped, which is what keeps the preset tables' `["key", value],` rows and
# everything inside a module body out of the parameter set.
DECL_START = re.compile(r"^(\$?[A-Za-z_][A-Za-z0-9_]*)\s*=")

# The Customizer's `// [min:step:max]` / `// [Option, Option]` annotation.
RANGE = re.compile(r"//\s*(\[[^\]]*\])")


def _body_from_marker(text: str) -> str:
    idx = text.index(BODY_MARKER)
    return text[idx:]


def _parameter_region(text: str) -> str:
    """Everything above the geometry body, with any inlined presets removed.

    The inlined block is compared against presets.scad separately - keeping it
    here would just report the two preset tables as MakerWorld-only parameters.
    """
    region = text[: text.index(BODY_MARKER)]
    if INLINE_BEGIN in region:
        head, _, rest = region.partition(INLINE_BEGIN)
        _, _, tail = rest.partition(INLINE_END)
        region = head + tail
    return region


def _declarations(region: str) -> dict:
    """Map every top-level `name = value;` to its value text and slider range.

    Values are collected across continuation lines up to the terminating `;`
    and whitespace-normalised, so re-wrapping an expression is not reported as
    drift but changing a number is.
    """
    decls = {}
    lines = region.split("\n")
    i = 0
    while i < len(lines):
        match = DECL_START.match(lines[i])
        if not match:
            i += 1
            continue
        name = match.group(1)
        chunk = lines[i][match.end() :]
        value_parts = []
        rng = None
        while True:
            code, sep, comment = chunk.partition("//")
            value_parts.append(code)
            if rng is None and sep:
                found = RANGE.search(sep + comment)
                if found:
                    rng = found.group(1)
            if ";" in code:
                break
            i += 1
            if i >= len(lines):
                break
            chunk = lines[i]
        value = " ".join(" ".join(value_parts).split())
        value = value[: value.index(";")].strip() if ";" in value else value.strip()
        assert name not in decls, f"`{name}` declared twice above the sync marker"
        decls[name] = (value, rng)
        i += 1
    return decls


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


def test_parameter_defaults_and_ranges_match():
    """Every declaration above the marker must carry the same value in both builds.

    This is the half the body guard cannot see. It covers the Customizer
    parameters (defaults AND `[min:step:max]` ranges), the double-sided tab, and
    the DOUBLE-SIDED (INTERPOINT) MATH constants - which
    tests/test_interpoint_math_scad.py otherwise checks in the canonical file
    only, so without this the flattened build could carry a different
    interpoint offset or footprint and nothing would notice.
    """
    canonical = _declarations(_parameter_region(CANONICAL.read_text(encoding="utf-8")))
    makerworld = _declarations(_parameter_region(MAKERWORLD.read_text(encoding="utf-8")))

    missing = sorted(set(canonical) - set(makerworld))
    extra = sorted(set(makerworld) - set(canonical))
    changed = sorted(
        f"{name}: canonical {canonical[name]!r} vs MakerWorld {makerworld[name]!r}"
        for name in set(canonical) & set(makerworld)
        if canonical[name] != makerworld[name]
    )

    assert not (missing or extra or changed), (
        "MakerWorld parameter declarations have drifted from the canonical file.\n"
        f"  missing from MakerWorld: {missing}\n"
        f"  only in MakerWorld: {extra}\n"
        f"  different value or range:\n    " + "\n    ".join(changed)
    )


def test_inlined_presets_match_presets_scad():
    """The pasted preset tables must still be what presets.scad says.

    The presets override the Customizer defaults the test above pins, so a stale
    paste here silently changes dot and bowl geometry on MakerWorld only.
    """
    makerworld = MAKERWORLD.read_text(encoding="utf-8")
    presets = PRESETS.read_text(encoding="utf-8")

    _, _, rest = makerworld.partition(INLINE_BEGIN)
    inlined, sentinel, _ = rest.partition(INLINE_END)
    assert sentinel, "MakerWorld file is missing the inlined-presets END sentinel"

    start = PRESET_BODY_MARKER.search(presets)
    assert start, "presets.scad is missing its own `/* [Hidden] */` marker"
    expected = presets[start.start() :]

    drift = "".join(
        difflib.unified_diff(
            inlined.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            "inlined in MakerWorld build",
            "presets.scad",
        )
    )
    assert not drift, (
        "The inlined presets.scad body in the MakerWorld build no longer matches "
        "presets.scad. Re-paste everything from that file's `/* [Hidden] */` "
        f"marker to EOF between the BEGIN/END sentinels.\n{drift}"
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


def test_dot_shape_defaults_to_rounded():
    """Both builds ship with the Rounded default (dropdown still offers Cone).

    Rounded is the default braille dot shape for the 0.4mm and 0.3mm presets."""
    makerworld = MAKERWORLD.read_text(encoding="utf-8")
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert 'dot_shape = "Rounded"; // [Rounded, Cone]' in makerworld
    assert 'dot_shape = "Rounded"; // [Rounded, Cone]' in canonical


def test_double_sided_tab_reaches_the_customizer():
    """The beta's controls must sit above the first `/* [Hidden] */` group.

    MakerWorld's Parametric Model Maker IS a Customizer, and the repo's
    parameter-schema validator stops parsing at the first Hidden group - so a
    control declared below one reaches neither. `ds_self_check` is the single
    deliberate exception: it is a test hook, not a user control.
    """
    makerworld = MAKERWORLD.read_text(encoding="utf-8")
    tab = makerworld.index("/* [Double-Sided Card (BETA)] */")
    first_hidden = makerworld.index("/* [Hidden] */")
    assert tab < first_hidden, (
        "The [Double-Sided Card (BETA)] tab must be declared above the first "
        "`/* [Hidden] */` group, or none of its controls reach MakerWorld's "
        "Customizer."
    )
    for name in ["double_sided = ", "interpoint_offset_x_mm = ", "interpoint_offset_y_mm = "] + [
        f"Back_Line_{n} = " for n in range(1, 11)
    ]:
        assert makerworld.index(name) < first_hidden, (
            f"`{name.strip(' =')}` is declared below the first `/* [Hidden] */` "
            "group, so MakerWorld's Customizer will never show it."
        )
