"""
The ``hemisphere_quality`` test override actually changes tessellation.

``quality_fn`` feeds ``$fn`` for the rounded dot's dome, and it has two inputs:
the user-facing ``render_quality`` dropdown (Low/Medium/High, shipped Medium)
and the ``[Hidden]`` ``hemisphere_quality`` override the test system uses to ask
for a specific tessellation without touching the dropdown.

Those two used to be interleaved in one ternary chain, and the interleaving had
a bug worth a permanent test: with the shipped ``render_quality = "Medium"``
standing, ``hemisphere_quality = "high"`` fell through the "low" arm, matched
``render_quality == "Medium"`` in the second arm, and returned 32. The 64 arm
could not be reached. ``"low"`` and ``"medium"`` looked fine - ``"low"`` wins its
arm outright and ``"medium"`` happens to collide with the default's own answer -
so the defect was invisible except on the single value that disagrees with the
default, and no fixture used that value.

The assertions are on triangle COUNT, deliberately, not on ``$fn`` appearing in
the source: the question is whether the exported mesh is actually tessellated
differently, which is the thing the override exists to control.

License: PolyForm Noncommercial 1.0.0
"""

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from test_gear_rollers_scad import _render, openscad_binary  # noqa: E402,F401

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# One short line on the default cylinder. Enough dots to make the dome count
# dominate the mesh, small enough to render quickly.
BASE_DEFINES = {
    "Line_1": "⠐⠑⠋⠋⠕",
    "Line_2": "",
    "plate_type": "positive",
    "dot_shape": "Rounded",
}


def _triangle_count(stl_path):
    """
    Triangles in an STL, ASCII or binary.

    Both branches are needed: this OpenSCAD writes ASCII by default, but the
    default has been announced as moving to binary, and --export-format can pick
    either. Sniffing the content rather than trusting the extension means the
    test keeps measuring the same thing when that changes.
    """
    data = stl_path.read_bytes()
    assert len(data) > 84, f"{stl_path} is too small to be an STL"

    if data[:5].lower() == b"solid" and b"facet normal" in data[:2048]:
        return data.count(b"facet normal")

    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50, (
        f"{stl_path} parses as neither ASCII nor binary STL: binary header says "
        f"{count} triangles, file is {len(data)} bytes"
    )
    return count


def _render_at(binary, tmp_path, quality):
    defines = dict(BASE_DEFINES)
    if quality is not None:
        defines["hemisphere_quality"] = quality
    stl_path, output, returncode = _render(
        binary, tmp_path, f"hq_{quality or 'default'}", defines
    )
    assert stl_path.exists(), (
        f"no STL written for hemisphere_quality={quality!r}:\n{output}"
    )
    assert "ERROR:" not in output, output
    assert "WARNING:" not in output, output
    return _triangle_count(stl_path)


@pytest.fixture(scope="module")
def counts(openscad_binary, tmp_path_factory):  # noqa: F811  (fixture request, not a redefinition)
    """All four renders once - each is a full plate and they are not cheap."""
    tmp_path = tmp_path_factory.mktemp("hemisphere_quality")
    return {
        quality: _render_at(openscad_binary, tmp_path, quality)
        for quality in (None, "low", "medium", "high")
    }


def test_high_is_finer_than_medium(counts):
    """The regression. Before the fix these two were byte-for-byte the same."""
    assert counts["high"] > counts["medium"], (
        "hemisphere_quality='high' produced no more triangles than 'medium' "
        f"({counts['high']} vs {counts['medium']}) - the override is being "
        "swallowed by the render_quality dropdown again"
    )


def test_low_is_coarser_than_medium(counts):
    assert counts["low"] < counts["medium"], (
        f"hemisphere_quality='low' ({counts['low']}) should be coarser than "
        f"'medium' ({counts['medium']})"
    )


def test_the_override_left_unset_matches_the_shipped_dropdown(counts):
    """
    No override must still mean the shipped Medium, or the fix moved the
    default rather than the override - which would change every export.
    """
    assert counts[None] == counts["medium"], (
        f"unset ({counts[None]}) no longer matches medium ({counts['medium']})"
    )
