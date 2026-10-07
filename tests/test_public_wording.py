"""
The public .scad files speak the web app's language (v2.9.0).

The web generator took double-sided cards and integrated gears out of beta on
2026-09-20, has built both cylinders by default since 2026-09-21, and names its
sections Card sides, Gears, Cylinders to Generate, Row Indicator Style and Card
Thickness - the last three inside Expert Mode, which the Customizer mirrors as
"Expert Mode - " tabs since 2026-10-07 (tests/test_customizer_layout.py pins
the whole order). These guards hold the files a user opens - the two desktop
files, their MakerWorld uploads and presets.scad - to the same terms:

* no BETA label anywhere;
* no internal sign-off bookkeeping (Brennen's rule, 2026-09-01): the
  Customizer shows the comment block above a dial as its description, so a
  label there reaches every user, and the wording pins live in these tests;
* the web app's section names, one Customizer tab each, above the first
  Hidden tab - Gears only in the desktop files, because MakerWorld cannot ship
  the gear meshes;
* both cylinders by default.

Source-only, so they run without OpenSCAD.

License: PolyForm Noncommercial 1.0.0
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESKTOP = [
    PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad",
    PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad",
]
MAKERWORLD = [
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad",
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad",
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2_Fixed_Gears.scad",
]
MODELS = DESKTOP + MAKERWORLD
PUBLIC_FILES = MODELS + [PROJECT_ROOT / "presets.scad"]

WEB_SECTIONS = [
    "/* [Card Sides] */",
    "/* [Expert Mode - Cylinders to Generate] */",
    "/* [Expert Mode - Row Indicator Style] */",
    "/* [Expert Mode - Card Thickness] */",
]
GEARS_SECTION = "/* [Gears] */"
RETIRED_SECTIONS = [
    "/* [Double-Sided Card",
    "/* [Integrated Gears",
    "/* [Plate Selection] */",
    "/* [Indicator Mode] */",
    "/* [Paper Thickness Preset] */",
    # Main tabs before 2026-10-07, when the web app's Expert Mode dials moved
    # under "Expert Mode - " tabs.
    "/* [Cylinders to Generate] */",
    "/* [Row Indicator Style] */",
    "/* [Card Thickness] */",
    "/* [Version 2 Keyed Cutouts] */",
    "/* [Rendering Quality] */",
    "/* [Expert Mode - Cylinder Dimensions] */",
]
DEVELOPMENT_TAGS = ("signed off", "sign-off", "reword only", "re-signed")


def _names(paths):
    return [path.name for path in paths]


@pytest.mark.parametrize("path", PUBLIC_FILES, ids=_names(PUBLIC_FILES))
def test_no_beta_label_remains(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [line for line in lines if re.search(r"\bbeta\b", line, re.IGNORECASE)]
    assert not hits, f"{path.name} still says beta: {hits[:3]}"


@pytest.mark.parametrize("path", PUBLIC_FILES, ids=_names(PUBLIC_FILES))
def test_no_development_tags_reach_the_public_file(path):
    lowered = path.read_text(encoding="utf-8").lower()
    for tag in DEVELOPMENT_TAGS:
        assert tag not in lowered, f"{tag!r} is back in {path.name}"
    assert not re.search(r"\(signed \d{4}-\d{2}-\d{2}\)", lowered), path.name


@pytest.mark.parametrize("path", MODELS, ids=_names(MODELS))
def test_the_sections_use_the_web_app_names(path):
    text = path.read_text(encoding="utf-8")
    first_hidden = text.index("/* [Hidden] */")
    for section in WEB_SECTIONS:
        assert text.count(section) == 1, f"{section} missing from {path.name}"
        assert text.index(section) < first_hidden, f"{section} is hidden in {path.name}"
    for retired in RETIRED_SECTIONS:
        assert retired not in text, f"{retired} is back in {path.name}"
    assert (GEARS_SECTION in text) == (path in DESKTOP), path.name


@pytest.mark.parametrize("path", MODELS, ids=_names(MODELS))
def test_both_cylinders_are_the_default(path):
    text = path.read_text(encoding="utf-8")
    assert text.count('render_both_plates = "On"; // [Off, On]') == 1, path.name
