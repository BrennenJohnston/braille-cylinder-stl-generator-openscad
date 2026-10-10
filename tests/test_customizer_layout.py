"""
The Customizer mirrors the web app's layout (Brennen's rule, 2026-10-07).

The dials follow the web generator's UI as closely as the Customizer allows:
its sections in its top-down order, under its names, and every dial the web
app keeps under Expert Mode in an "Expert Mode - " tab. A dial the web app
does not have sits at the end of the section it belongs to, or in one of the
two OpenSCAD-only tabs after the mirrored ones.

The web app's order, top to bottom (public/index.html in
braille-cylinder-stl-generator, 2026-10-07):

* Embosser setup: Embosser version (no Customizer counterpart - each version
  is its own file), Gears, Card sides;
* Enter Text for Braille Translation, then Back of Card;
* Expert Mode: Cylinders to Generate, Card Thickness, Row Indicator Style,
  Shape Selection, Braille Spacing, Braille Dot Adjustments, Surface
  Dimensions (with its Slicer Seam Channel and Version 2 Keyed Cutouts).

When the web app's layout changes, change LAYOUT below and the model files
in the same round.

The second rule here is about descriptions. OpenSCAD and MakerWorld show only
the ONE comment line directly above a dial as its description, so a wrapped
comment reached users as its last fragment ("exactly as they are.", "fixed in
the Hidden section below."), and a section label directly above a dial became
that dial's description. Every visible dial's description is one line, and a
URL in it carries no scheme, because the Customizer cuts a description at
"//".

Source-only, so it runs without OpenSCAD.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GROUP = re.compile(r"^/\* \[(.+)\] \*/$")
DECL = re.compile(r"^(\$?[A-Za-z_]\w*)\s*=")

GEARS = [("Gears", ["integrated_gears"])]
CARD_SIDES = [("Card Sides", ["double_sided"])]
CYLINDERS = [("Expert Mode - Cylinders to Generate", ["render_both_plates", "plate_type", "pair_spacing_mm"])]
MIDDLE = [
    ("Expert Mode - Card Thickness", ["paper_thickness_preset"]),
    (
        "Expert Mode - Row Indicator Style",
        [
            "indicator_mode",
            "tactile_indicator_width",
            "tactile_indicator_length",
            "tactile_indicator_raise",
            "tactile_recess_clearance",
            "tactile_recess_extra_depth",
        ],
    ),
    ("Expert Mode - Shape Selection", ["dot_shape", "indicators"]),
    (
        "Expert Mode - Braille Spacing",
        ["grid_columns", "grid_rows", "cell_spacing", "line_spacing", "dot_spacing", "braille_y_adjust", "text_limit_check"],
    ),
    (
        "Expert Mode - Braille Dot Adjustments",
        [
            "rounded_dot_base_diameter",
            "rounded_dot_base_height",
            "rounded_dot_dome_diameter",
            "rounded_dot_dome_height",
            "emboss_dot_base_diameter",
            "emboss_dot_height",
            "emboss_dot_flat_hat",
            "bowl_counter_dot_base_diameter",
            "counter_dot_depth",
            "cone_counter_dot_base_diameter",
            "cone_counter_dot_height",
            "cone_counter_dot_flat_hat",
        ],
    ),
]
OPENSCAD_ONLY = [
    ("Expert Mode - Card Sides", ["interpoint_offset_x_mm", "interpoint_offset_y_mm"]),
    ("Expert Mode - Rendering Quality", ["render_quality", "cone_segments"]),
]


def _lines(prefix, count):
    return [f"{prefix}{n}" for n in range(1, count + 1)]


def version1(makerworld):
    return (
        ([] if makerworld else GEARS)
        + CARD_SIDES
        + [
            ("Text Input - Pre-Translated Braille", _lines("Line_", 8)),
            ("More Braille Lines (Advanced)", ["Line_9", "Line_10"]),
            ("Back of Card - Pre-Translated Braille", _lines("Back_Line_", 10)),
        ]
        + CYLINDERS
        + MIDDLE
        + [
            (
                "Expert Mode - Surface Dimensions",
                [
                    "cylinder_diameter_mm",
                    "cylinder_height_mm",
                    "polygon_cutout_radius_mm",
                    "polygon_cutout_points",
                    "seam_offset_degrees",
                    "seam_channel",
                ],
            )
        ]
        + OPENSCAD_ONLY
    )


def version2(makerworld):
    return (
        ([] if makerworld else GEARS)
        + CARD_SIDES
        + [
            ("Text Input - Pre-Translated Braille", _lines("Line_", 4)),
            ("Back of Card - Pre-Translated Braille", _lines("Back_Line_", 4)),
        ]
        + CYLINDERS
        + MIDDLE
        + [
            ("Expert Mode - Surface Dimensions", ["cylinder_diameter_mm", "cylinder_height_mm", "seam_channel"]),
            ("Expert Mode - Version 2 Keyed Cutouts", _keys()),
        ]
        + OPENSCAD_ONLY
    )


def _keys():
    return [f"key_clearance_{gear}_mm" for gear in ("a1", "a2", "b1", "b2")]


def version2_fixed_gears():
    """The fixed-gear upload hides the size and the clearances (see its header)."""
    layout = []
    for group, dials in version2(makerworld=True):
        if group == "Expert Mode - Version 2 Keyed Cutouts":
            continue
        if group == "Expert Mode - Surface Dimensions":
            dials = ["seam_channel"]
        layout.append((group, dials))
    return layout


LAYOUT = {
    "Braille_Cylinder_STL_Generator.scad": version1(makerworld=False),
    "makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad": version1(makerworld=True),
    "Braille_Cylinder_STL_Generator_EmbosserV2.scad": version2(makerworld=False),
    "makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2.scad": version2(makerworld=True),
    "makerworld/Braille_Cylinder_STL_Generator_MakerWorld_v2_Fixed_Gears.scad": version2_fixed_gears(),
}


def _visible(text):
    """The Customizer region: group headers and declarations above the first Hidden tab."""
    region = text[: text.index("/* [Hidden] */")]
    lines = region.split("\n")
    layout, dials = [], []
    for i, line in enumerate(lines):
        group = GROUP.match(line)
        if group:
            layout.append((group.group(1), []))
            continue
        decl = DECL.match(line)
        if decl and layout:
            layout[-1][1].append(decl.group(1))
            above = []
            j = i - 1
            while j >= 0 and lines[j].startswith("//"):
                above.insert(0, lines[j])
                j -= 1
            dials.append((decl.group(1), above))
    return layout, dials


@pytest.mark.parametrize("rel", sorted(LAYOUT))
def test_the_tabs_follow_the_web_app_order(rel):
    layout, _ = _visible((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
    expected = LAYOUT[rel]
    assert [g for g, _ in layout] == [g for g, _ in expected], (
        f"{rel}: the Customizer tabs are out of the web app's order.\n"
        f"  found:    {[g for g, _ in layout]}\n"
        f"  expected: {[g for g, _ in expected]}"
    )
    for (group, dials), (_, want) in zip(layout, expected):
        assert dials == want, f"{rel} [{group}]: dials {dials}, expected {want}"


@pytest.mark.parametrize("rel", sorted(LAYOUT))
def test_every_description_is_one_line(rel):
    _, dials = _visible((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
    wrapped = [name for name, above in dials if len(above) > 1]
    assert not wrapped, (
        f"{rel}: the Customizer shows only the last line of these descriptions: "
        f"{wrapped}. Put each on one line, or move the extra lines above a blank line."
    )
    labels = [name for name, above in dials if above and above[0].startswith("// ---")]
    assert not labels, f"{rel}: a section label is the description of {labels}"
    schemes = [name for name, above in dials if above and "://" in above[0]]
    assert not schemes, f"{rel}: the Customizer cuts these descriptions at '//': {schemes}"


# Brennen's shortened wording (2026-10-07) for the five descriptions the
# Customizer's wrapping cut short; each was signed on its own.
SIGNED = {
    "double_sided": (
        "On embosses both faces of the card in one pass; the back's braille goes in the Back of Card "
        "group. Each cylinder then carries raised dots and recesses, and the rows get the tactile arrows."
    ),
    "Back_Line_1": (
        "The back of the card, one row per field, in the same order as the front: Unicode braille, "
        "translated the same way. Used only while double sided is On."
    ),
    "render_both_plates": (
        "On builds Cylinder A (left) and Cylinder B (right) in one file, spaced for one print plate. "
        "Off builds only the one that plate type names."
    ),
}
INDICATOR = {
    2: (
        "Tactile (default): a raised arrow on Cylinder A and a matching recess on Cylinder B, found by "
        "touch; uses no braille cells. Visual: a recessed triangle, plus the optional letter square, at "
        "the start of each row."
    ),
    1: (
        "Visual (default): a recessed triangle, plus the optional letter square, at the start of each "
        "row. Tactile: a raised arrow on Cylinder A and a matching recess on Cylinder B, found by touch; "
        "uses no braille cells."
    ),
}
GEARS = {
    "Braille_Cylinder_STL_Generator_EmbosserV2.scad": (
        "Makes each cylinder one solid piece with its top and bottom gears; needs the assets folder "
        "beside this file. Fixed gears fit only the fixed-gear housing; the standard housing takes the "
        "standard cylinders."
    ),
    "Braille_Cylinder_STL_Generator.scad": (
        "Makes each cylinder one solid piece with its top and bottom gears; needs the assets folder "
        "beside this file. Fixed gears fit only the Version 1 fixed-gear housing; the standard housing "
        "takes the standard cylinders."
    ),
}


@pytest.mark.parametrize("rel", sorted(LAYOUT))
def test_the_signed_descriptions(rel):
    _, dials = _visible((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
    shown = {name: (above[0][3:] if above else "") for name, above in dials}
    version = 2 if "EmbosserV2" in rel or "_v2" in rel else 1
    expected = dict(SIGNED, indicator_mode=INDICATOR[version])
    if rel in GEARS:
        expected["integrated_gears"] = GEARS[rel]
    for name, text in expected.items():
        assert shown.get(name) == text, f"{rel}: {name} reads {shown.get(name)!r}"
