"""
DOT_BASE_EMBED — raised dots are fused to the cylinder shell.

The shell is a 64-sided prism, so each facet dips inside the ideal radius at its
centre. Until 2026-08-21 a raised dot's flat base sat at exactly that ideal
radius, spanning the dip instead of biting into it, and every dot exported as
its own connected body: 32 bodies on the single-sided default (1 shell + 31
dots), 6 and 9 on the double-sided pair. `DOT_BASE_EMBED` now lengthens each
dot's base frustum downward along its own taper so it overlaps solid shell.

Two invariants, and the second is the one that matters most:

1. Every plate exports as ONE connected body.
2. The dot still stands exactly as far proud of the shell as it always did.
   The skirt goes DOWN only. Dot height is a tactile accessibility dimension —
   if this test goes red, the fix has started changing what a reader feels.

The double-sided plates are covered by the matching pair of tests in
``tests/test_double_sided.py::TestGoldenTopology``; this file covers the
single-sided renders, which is every plate the project shipped before the beta.

License: PolyForm Noncommercial 1.0.0
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_double_sided import _preset_value  # noqa: E402  (shared helper)
from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAD_FILE = PROJECT_ROOT / "Braille_Cylinder_STL_Generator.scad"

# Only Line_1 is filled: the file ships demo text in Line_2 as well, which would
# render a second band of dots and make the body count harder to read.
BRAILLE_TEXT = "⠁⠃⠉"  # a b c

# A $fn sphere puts no vertex exactly on its pole, so a rendered dome lands just
# under nominal - 0.0023 mm on the 0.4 package at the default sphere quality.
# The cone family has a flat hat instead, whose rim sits slightly FURTHER from
# the axis than the hat centre; that offset is computed exactly below, so it
# needs only float slack.
DOME_TESSELLATION_SLACK_MM = 0.006
CONE_RIM_SLACK_MM = 0.001


@pytest.fixture(scope="module")
def runner():
    from openscad_runner import OpenSCADNotFoundError, OpenSCADRunner

    try:
        return OpenSCADRunner(openscad_path=_resolve_openscad_path())
    except OpenSCADNotFoundError as exc:
        pytest.skip(f"OpenSCAD not available for the dot-embed tests: {exc}")


@pytest.fixture(scope="module")
def trimesh_module():
    try:
        import trimesh
    except ImportError:
        pytest.skip("trimesh is not installed; skipping the dot-embed render tests")
    return trimesh


def _render(runner, tmp_path, preset, dot_shape):
    stl_path = tmp_path / f"embed_{preset}_{dot_shape}.stl".replace(".", "_", 1)
    result = runner.generate_stl(
        scad_file=SCAD_FILE,
        output_stl=stl_path,
        parameters={
            "paper_thickness_preset": preset,
            "dot_shape": dot_shape,
            "Line_1": BRAILLE_TEXT,
            "Line_2": "",
        },
        timeout_seconds=300,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.success, f"OpenSCAD failed on {preset}/{dot_shape}: {output[:800]}"
    assert "WARNING:" not in output and "ERROR:" not in output, (
        f"{preset}/{dot_shape} did not render clean:\n{output[:800]}"
    )
    return stl_path


# (paper_thickness_preset, dot_shape, PRESET table name)
CONFIGURATIONS = [
    ("0.4mm", "Rounded", "PRESET_04"),
    ("0.4mm", "Cone", "PRESET_04"),
    ("0.3mm", "Rounded", "PRESET_03"),
    ("0.3mm", "Cone", "PRESET_03"),
]


@pytest.mark.parametrize("preset,dot_shape,table", CONFIGURATIONS)
def test_a_single_sided_plate_is_one_connected_body(
    runner, trimesh_module, tmp_path_factory, preset, dot_shape, table
):
    """No dot may float above the shell facet it sits on."""
    tmp_path = tmp_path_factory.mktemp("dot_embed")
    mesh = trimesh_module.load(_render(runner, tmp_path, preset, dot_shape))
    bodies = mesh.split(only_watertight=False)
    assert len(bodies) == 1, (
        f"The {preset} {dot_shape} emboss plate split into {len(bodies)} connected "
        "bodies; DOT_BASE_EMBED is supposed to fuse every raised dot to the shell. "
        f"Body sizes (facets): {sorted(len(b.faces) for b in bodies)}"
    )
    assert mesh.is_watertight, f"The {preset} {dot_shape} emboss plate is not watertight."


@pytest.mark.parametrize("preset,dot_shape,table", CONFIGURATIONS)
def test_the_embed_did_not_change_how_far_a_dot_stands_proud(
    runner, trimesh_module, tmp_path_factory, preset, dot_shape, table
):
    """
    TACTILE ACCESSIBILITY GUARD. The embed lengthens the dot's base DOWNWARD
    into the shell; every surface at or above the shell must be exactly where it
    was. The furthest vertex from the cylinder axis is the top of the tallest
    dot, so pinning it pins the standing height.

    Expected values come from the preset table, never from a recorded
    measurement, so changing a preset moves the test with the geometry.
    """
    import numpy as np

    tmp_path = tmp_path_factory.mktemp("dot_embed_height")
    mesh = trimesh_module.load(_render(runner, tmp_path, preset, dot_shape))
    apex = float(np.hypot(mesh.vertices[:, 0], mesh.vertices[:, 1]).max())

    radius = _preset_value("cylinder_diameter_mm", table=table) / 2
    if dot_shape == "Rounded":
        nominal = _preset_value("rounded_dot_base_height", table=table) + _preset_value(
            "rounded_dot_dome_height", table=table
        )
        low, high = nominal - DOME_TESSELLATION_SLACK_MM, nominal
        expected = f"{nominal} mm (tessellated dome, so just under)"
    else:
        height = _preset_value("emboss_dot_height", table=table)
        hat_radius = _preset_value("emboss_dot_flat_hat", table=table) / 2
        # The hat is a flat disc facing radially outward; its RIM is further from
        # the cylinder axis than its centre by exactly this much.
        nominal = math.hypot(radius + height, hat_radius) - radius
        low, high = nominal - CONE_RIM_SLACK_MM, nominal + CONE_RIM_SLACK_MM
        expected = f"{nominal:.5f} mm (flat hat, measured at its rim)"

    proud = apex - radius
    print()
    print(f"{preset} {dot_shape}: tallest dot stands {proud:.5f} mm proud, expected {expected}")
    assert low <= proud <= high, (
        f"The {preset} {dot_shape} dot now stands {proud:.5f} mm proud of the shell, "
        f"outside [{low:.5f}, {high:.5f}]. Dot height is a tactile dimension: the base "
        "embed is allowed to add material below the surface only."
    )
