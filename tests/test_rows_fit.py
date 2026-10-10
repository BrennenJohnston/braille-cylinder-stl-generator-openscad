"""
Rows fit - the OpenSCAD side of the web generator's Rows-limit fix (2026-10-09).

The web generator refuses rows whose dots would run off the card, or whose
per-row tactile arrows would run off the barrel (app/validation.py
validate_braille_rows_fit, from app/geometry_spec.py braille_rows_extent), and
Brennen chose the same check here. The four model files carry one identical
block that stops the model with the web generator's two sentences. These tests
pin the block, the sentences and the constants against the web repository
(a sibling checkout, or BRAILLE_WEB_REPO; skipped loudly when absent), and
evaluate the models on the cases the web repository's tests/test_rows_limit.py
uses. Verdicts come from the output text, never from an exit code.

License: PolyForm Noncommercial 1.0.0
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"
V2_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator_EmbosserV2.scad"
MODELS = [
    V1_FILE,
    V2_FILE,
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v1.5.scad",
    PROJECT_ROOT / "makerworld" / "Braille_Cylinder_STL_Generator_MakerWorld_v2.scad",
]
WEB_REPO = Path(
    os.environ.get(
        "BRAILLE_WEB_REPO", str(PROJECT_ROOT.parent / "braille-cylinder-stl-generator")
    )
)

# The tails of the web generator's two sentences (S-R2: the card, S-R1: the
# barrel), word for word.
CARD_TAIL = "mm height, so the top and bottom rows would run off the card. Use fewer rows or a smaller line spacing."
BARREL_TAIL = (
    "mm height, so the top and bottom rows would run off the ends. "
    "Use fewer rows, a smaller line spacing, or a taller cylinder."
)

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)


def _block(text):
    start = text.index("// Rows fit (Brennen, 2026-10-09)")
    end_marker = 'a taller cylinder."));'
    return text[start : text.index(end_marker, start) + len(end_marker)]


def test_the_four_models_carry_the_same_block():
    blocks = {path.name: _block(path.read_text(encoding="utf-8")) for path in MODELS}
    assert len(set(blocks.values())) == 1, sorted(blocks)
    block = next(iter(blocks.values()))
    assert "CARD_HEIGHT_MM = 52;" in block
    assert '" mm height, so the top and bottom rows would run off the card. ",' in block
    assert '"Use fewer rows or a smaller line spacing."' in block
    assert '"Use fewer rows, a smaller line spacing, or a taller cylinder."' in block


def test_the_constants_and_sentences_match_the_web_generator():
    validation = WEB_REPO / "app" / "validation.py"
    models = WEB_REPO / "app" / "models.py"
    if not validation.exists():
        pytest.skip(f"web repository not found at {WEB_REPO} (set BRAILLE_WEB_REPO)")
    web = validation.read_text(encoding="utf-8")
    if "def validate_braille_rows_fit" not in web:
        pytest.skip(
            f"the web repository at {WEB_REPO} predates the rows-fit rule (its PR #116)"
        )
    assert (
        "'height, so the top and bottom rows would run off the card. Use fewer rows or a smaller line spacing.'"
        in web
    )
    assert "mm height, so the top and bottom rows would run off the ends. '" in web
    assert "'Use fewer rows, a smaller line spacing, or a taller cylinder.'" in web
    card = re.search(r"'card_height': ([0-9.]+),", models.read_text(encoding="utf-8"))
    assert card and float(card.group(1)) == 52.0
    gears = (WEB_REPO / "app" / "geometry" / "gears.py").read_text(encoding="utf-8")
    weld = re.search(r"^GEAR_ARROW_WELD_MM = ([0-9.]+)", gears, re.MULTILINE)
    scad_weld = re.search(
        r"^GEAR_ARROW_WELD_MM = ([0-9.]+);",
        V1_FILE.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert weld and scad_weld and float(weld.group(1)) == float(scad_weld.group(1))


@pytest.fixture(scope="module")
def openscad_binary():
    resolved = _resolve_openscad_path()
    for candidate in (
        [Path(str(resolved).replace(".exe", ".com")), Path(resolved)]
        if resolved
        else []
    ):
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the rows-fit tests")


def _evaluate(binary, model, tmp_path, *defines):
    """The model's assertion message, or '' when it evaluates cleanly."""
    echo = tmp_path / "rows.echo"
    command = [
        str(binary),
        "-D",
        'paper_thickness_preset="Custom"',
        "-D",
        'render_both_plates="Off"',
    ]
    for define in defines:
        command += ["-D", define]
    command += ["-o", str(echo), str(model)]
    subprocess.run(
        command, capture_output=True, text=True, timeout=300, cwd=PROJECT_ROOT
    )
    text = echo.read_text(encoding="utf-8") if echo.exists() else ""
    failed = re.search(r'failed: "([^"]*)"', text)
    return failed.group(1) if failed else ""


@pytest.mark.parametrize(
    ("model", "defines", "expected"),
    [
        (V1_FILE, ("grid_rows=5",), ""),
        (
            V1_FILE,
            ("grid_rows=6",),
            f"These 6 rows need 56.8 mm of the cylinder's 52 {BARREL_TAIL}",
        ),
        (V1_FILE, ("grid_rows=4", 'indicator_mode="Tactile"'), ""),
        (
            V1_FILE,
            ("grid_rows=5", 'indicator_mode="Tactile"'),
            f"These 5 rows need 52.04 mm of the cylinder's 52 {BARREL_TAIL}",
        ),
        (
            V1_FILE,
            ("grid_rows=4", "braille_y_adjust=10"),
            f"These 4 rows need 56.8 mm of the cylinder's 52 {BARREL_TAIL}",
        ),
        (V1_FILE, ("grid_rows=6", "line_spacing=9"), ""),
        (
            V1_FILE,
            ("grid_rows=6", "cylinder_height_mm=60"),
            f"These 6 rows need 56.8 mm of the card's 52 {CARD_TAIL}",
        ),
        (V2_FILE, ("grid_rows=4", 'indicator_mode="Tactile"'), ""),
    ],
    ids=[
        "v1-visual-5",
        "v1-visual-6",
        "v1-tactile-4",
        "v1-tactile-5",
        "v1-y-adjust",
        "v1-spacing-9",
        "v1-60mm-card",
        "v2-tactile-4",
    ],
)
def test_the_models_refuse_the_rows_the_web_generator_refuses(
    openscad_binary, tmp_path, model, defines, expected
):
    assert _evaluate(openscad_binary, model, tmp_path, *defines) == expected
