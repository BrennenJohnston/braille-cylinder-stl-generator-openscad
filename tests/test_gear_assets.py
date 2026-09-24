"""
Gear assets — the vendored one-piece roller gears, in this repo's frame.

The gears are a 1:1 replication of Brennen's reference set. They are DERIVED,
never authored: the web repo (braille-cylinder-stl-generator) owns the
derivation in ``scripts/derive_gear_assets.py``, which reads the four reference
STLs and bakes the canonical sample-to-program transform into packed binaries at
``static/assets/gears/gears_{a,b}.bin``.

This repo needs the same geometry as STL, because ``.scad`` can only
``import()`` a mesh file — and in THIS generator's frame, which differs from the
browser's by the z seat alone. The browser centres a cylinder on z=0 (barrel
z -26..+26, gears -36..-26 and +26..+36); this generator seats the barrel base
at z=0, so the assets here are the same baked geometry translated **+26.000 mm
in z**: gears at z -10..0 and 52..62, axis at the origin, rotations identical.

``regenerate()`` below is the only supported way to rewrite ``assets/*.stl``.
Run it from the repo root when — and only when — the web repo's .bin assets
change:

    python -m tests.test_gear_assets

The web repo is NOT modified by this: its derivation script has no
OpenSCAD-frame output flag, so the conversion lives here, reading its bytes.

License: PolyForm Noncommercial 1.0.0
"""

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
PROVENANCE_PATH = ASSETS_DIR / "GEARS_PROVENANCE.json"
ASSET_NAMES = ("gears_a", "gears_b")
# The Embosser Version 2 fixed-gear pair (OpenSCAD parity plan phase O4,
# 2026-09-21), derived by the web repo's scripts/derive_gear_assets_v2.py from
# Brennen's v8 Version 2 gears with every axis measured per gear. Same packed
# format, same teeth and tip radius; a 54 mm barrel, so the frame shift and
# the z bands differ - see V2_Z_SHIFT_MM and V2_EXPECTED_Z_BANDS below.
V2_ASSET_NAMES = ("v2_gears_a", "v2_gears_b")
ALL_ASSET_NAMES = ASSET_NAMES + V2_ASSET_NAMES

# Where the derived binaries live. Only regenerate() needs this; the tests read
# this repo's own STLs and its provenance file, so the suite passes on a machine
# that does not have the web repo checked out.
#
# The literal is one machine's layout, which is fine for the tests (they never
# touch it) but makes regenerate() unrunnable anywhere else. BRAILLE_WEB_REPO
# overrides it; unset, the path below is used exactly as before.
WEB_REPO = Path(
    os.environ.get(
        "BRAILLE_WEB_REPO",
        r"C:\Users\WATAP\Documents\github\braille-cylinder-stl-generator",
    )
)
WEB_ASSETS_DIR = WEB_REPO / "static" / "assets" / "gears"

# The web repo's packed format. The header is 14 bytes, which is not a multiple
# of 4 — numpy.frombuffer takes that offset without complaint (only a browser's
# typed-array view would refuse it).
GEAR_MAGIC = b"BCGR1\x00"
GEAR_HEADER_BYTES = 14

# The only difference between the two repos' frames.
Z_SHIFT_MM = 26.000

# Gear metrology, measured from the reference set (research folder
# 01_SAMPLE_GEOMETRY_AUDIT.md section 3) and mirrored from the web repo's
# app/geometry/gears.py.
TOOTH_COUNT = 24
TIP_RADIUS_MM = 16.1093702290795
TIP_RADIUS_TOL_MM = 0.001
TIP_BAND_DEPTH_MM = 0.05
TOOTH_GAP_DEG = 2.0

# In this frame: a 10 mm gear below the barrel and another above it.
EXPECTED_Z_BANDS = ((-10.000, 0.000), (52.000, 62.000))

# Version 2: the browser centres its 54 mm barrel on z 0 (-27..+27), so the
# shift is +27.000 and the gear bodies sit at z -10..0 and 54..64. Unlike the
# Version 1 set, each gear carries a 15 mm keyed peg that lies INSIDE the
# barrel (z 0..15 and 39..54), never wider than 10.7 mm from the axis.
V2_Z_SHIFT_MM = 27.000
V2_EXPECTED_Z_BANDS = ((-10.000, 0.000), (54.000, 64.000))
V2_PEG_LENGTH_MM = 15.0
V2_PEG_MAX_RADIUS_MM = 10.7
V2_BARREL_HEIGHT_MM = 54.0
# The bottom gear of each set also carries a 3 mm anti-rotation PIN on its
# barrel-facing face (A the triangle, B the square, both reaching 13.85 mm on
# the 180 degree column - app/geometry/version2.py V2_GEAR_ANTIROT), which the
# barrel's socket receives; it sits in the first 3 mm above the face.
V2_PIN_HEIGHT_MM = 3.0
V2_PIN_MAX_RADIUS_MM = 13.9

# One row per asset set: which web assets, which frame shift, which bands.
ASSET_SETS = (
    {
        "names": ASSET_NAMES,
        "z_shift_mm": Z_SHIFT_MM,
        "bands": EXPECTED_Z_BANDS,
        "manifest": "gears_manifest.json",
        "provenance_key": "source_samples",
    },
    {
        "names": V2_ASSET_NAMES,
        "z_shift_mm": V2_Z_SHIFT_MM,
        "bands": V2_EXPECTED_Z_BANDS,
        "manifest": "v2_gears_manifest.json",
        "provenance_key": "v2_source_samples",
    },
)


def _bands(asset_name):
    return V2_EXPECTED_Z_BANDS if asset_name in V2_ASSET_NAMES else EXPECTED_Z_BANDS


BOUNDS_TOL_MM = 0.001
XY_LIMIT_MM = 16.110


def _read_packed(path):
    """Read one of the web repo's .bin assets into (vertices, faces)."""
    data = path.read_bytes()
    if data[:6] != GEAR_MAGIC:
        raise ValueError(
            f"{path.name}: bad magic {data[:6]!r}, expected {GEAR_MAGIC!r}"
        )
    vert_count, tri_count = struct.unpack_from("<II", data, 6)
    vertices = np.frombuffer(
        data, dtype="<f4", count=3 * vert_count, offset=GEAR_HEADER_BYTES
    )
    faces = np.frombuffer(
        data,
        dtype="<u4",
        count=3 * tri_count,
        offset=GEAR_HEADER_BYTES + 12 * vert_count,
    )
    return (
        vertices.reshape(-1, 3).astype(np.float64),
        faces.reshape(-1, 3).astype(np.int64),
    )


def regenerate():
    """Convert the web repo's .bin assets into this repo's frame as binary STLs."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    provenance = {
        "note": (
            "Derived 1:1 from Brennen's reference STLs; never edit; regenerate via the web "
            "repo's scripts/derive_gear_assets.py, then this repo's "
            "python -m tests.test_gear_assets"
        ),
        "derived": "2026-08-24",
        "frame": (
            "This generator's frame: cylinder axis at the origin, barrel base at z=0 "
            "(barrel z 0..52), gears at z -10..0 and 52..62. That is the web repo's "
            "browser frame translated +26.000 mm in z; rotations are identical (the A set "
            "carries the canonical Rz(180) rotation, the B set the identity)."
        ),
        "z_shift_mm": Z_SHIFT_MM,
        "source_repo": "braille-cylinder-stl-generator",
        "v2": {
            "note": (
                "The Embosser Version 2 fixed-gear pair, derived the same way from the web "
                "repo's static/assets/gears/v2_gears_{a,b}.bin (scripts/derive_gear_assets_v2.py, "
                "Brennen's v8 Version 2 gears, every axis measured per gear)."
            ),
            "derived": "2026-09-21",
            "frame": (
                "This generator's frame for the 54 mm Version 2 barrel: axis at the origin, "
                "barrel base at z=0 (barrel z 0..54), gear bodies at z -10..0 and 54..64, the "
                "15 mm keyed pegs inside the barrel at z 0..15 and 39..54. That is the web "
                "repo's browser frame translated +27.000 mm in z; rotations are identical."
            ),
            "z_shift_mm": V2_Z_SHIFT_MM,
        },
        "assets": {},
    }

    for asset_set in ASSET_SETS:
        web_manifest = json.loads(
            (WEB_ASSETS_DIR / asset_set["manifest"]).read_text(encoding="utf-8")
        )
        provenance[asset_set["provenance_key"]] = {
            name: entry["sources"] for name, entry in web_manifest["assets"].items()
        }
        for asset_name in asset_set["names"]:
            _derive_one(asset_name, asset_set["z_shift_mm"], provenance)

    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {PROVENANCE_PATH}")


def _derive_one(asset_name, z_shift_mm, provenance):
    """Shift one packed web asset into this frame and record it in the provenance."""
    import trimesh

    source = WEB_ASSETS_DIR / f"{asset_name}.bin"
    payload = source.read_bytes()
    vertices, faces = _read_packed(source)
    vertices[:, 2] += z_shift_mm

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    out_path = ASSETS_DIR / f"{asset_name}.stl"
    out_path.write_bytes(mesh.export(file_type="stl"))

    bodies = mesh.split(only_watertight=False)
    provenance["assets"][f"{asset_name}.stl"] = {
        "derived_from": f"static/assets/gears/{asset_name}.bin",
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        "byte_size": out_path.stat().st_size,
        "vert_count": int(len(vertices)),
        "tri_count": int(len(faces)),
        "body_count": len(bodies),
        "bounds_mm": {
            "min": [round(float(v), 6) for v in mesh.bounds[0]],
            "max": [round(float(v), 6) for v in mesh.bounds[1]],
        },
        "volume_mm3": round(float(mesh.volume), 6),
    }
    print(
        f"{asset_name}.stl: {len(faces)} triangles, volume {mesh.volume:.3f} mm^3, "
        f"z {mesh.bounds[0][2]:.3f}..{mesh.bounds[1][2]:.3f}"
    )


@pytest.fixture(scope="module")
def provenance():
    if not PROVENANCE_PATH.is_file():
        pytest.fail(
            f"{PROVENANCE_PATH} is missing. Regenerate with: python -m tests.test_gear_assets"
        )
    return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))


# This repo tracks *.stl through Git LFS, so a clone without LFS leaves a small
# text pointer where the mesh should be. Saying so plainly beats a hash mismatch
# or a parse error that reads like a corrupt asset.
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _require_real_asset(path):
    if not path.is_file():
        pytest.fail(
            f"{path} is missing. Regenerate with: python -m tests.test_gear_assets"
        )
    payload = path.read_bytes()
    if payload.startswith(LFS_POINTER_PREFIX):
        pytest.fail(f"{path} is a Git LFS pointer, not the mesh. Run: git lfs pull")
    return payload


def _load(asset_name):
    trimesh = pytest.importorskip("trimesh")
    path = ASSETS_DIR / f"{asset_name}.stl"
    _require_real_asset(path)
    return trimesh.load(str(path), file_type="stl", force="mesh")


def _tooth_clusters(vertices, z_low, z_high):
    """
    Count teeth in one gear band by clustering tip-band vertex angles.

    These meshes carry vertices only on feature edges, so a mid-band slice finds
    nothing: the tip band is the one radius where every tooth is guaranteed to
    have vertices.
    """
    in_band = vertices[(vertices[:, 2] > z_low) & (vertices[:, 2] < z_high)]
    radius = np.hypot(in_band[:, 0], in_band[:, 1])
    tips = in_band[radius > (TIP_RADIUS_MM - TIP_BAND_DEPTH_MM)]
    if len(tips) == 0:
        return 0
    angles = np.sort(np.degrees(np.arctan2(tips[:, 1], tips[:, 0])) % 360.0)
    gaps = np.diff(np.concatenate([angles, [angles[0] + 360.0]]))
    return max(1, int((gaps > TOOTH_GAP_DEG).sum()))


@pytest.mark.parametrize("asset_name", ALL_ASSET_NAMES)
def test_asset_bytes_match_the_provenance(asset_name, provenance):
    """
    The assets are a 1:1 replication and only one route may rewrite them. Pinning
    both hashes means a hand-edit, or a re-derivation from different source
    bytes, fails here rather than reaching a printer.
    """
    recorded = provenance["assets"][f"{asset_name}.stl"]
    payload = _require_real_asset(ASSETS_DIR / f"{asset_name}.stl")

    assert hashlib.sha256(payload).hexdigest() == recorded["sha256"]
    assert len(payload) == recorded["byte_size"]
    # Binary STL: 80-byte header, uint32 triangle count, 50 bytes per triangle.
    assert struct.unpack_from("<I", payload, 80)[0] == recorded["tri_count"]
    assert len(payload) == 84 + 50 * recorded["tri_count"]


@pytest.mark.parametrize("asset_name", ALL_ASSET_NAMES)
def test_asset_sits_in_this_repo_frame(asset_name):
    """Barrel base at z=0 means gears at z -10..0 and 52..62, axis at the origin."""
    mesh = _load(asset_name)
    low, high = mesh.bounds

    bands = _bands(asset_name)
    assert low[2] == pytest.approx(bands[0][0], abs=BOUNDS_TOL_MM)
    assert high[2] == pytest.approx(bands[1][1], abs=BOUNDS_TOL_MM)

    for axis in (0, 1):
        assert low[axis] >= -XY_LIMIT_MM
        assert high[axis] <= XY_LIMIT_MM


@pytest.mark.parametrize("asset_name", ALL_ASSET_NAMES)
def test_asset_is_two_watertight_gears(asset_name):
    """One gear for each end of the barrel, each a closed solid."""
    mesh = _load(asset_name)
    mesh.merge_vertices()
    bodies = mesh.split(only_watertight=False)

    assert len(bodies) == 2
    assert all(body.is_watertight for body in bodies)
    assert all(body.volume > 0 for body in bodies)

    spans = sorted(
        (round(float(b.bounds[0][2]), 3), round(float(b.bounds[1][2]), 3))
        for b in bodies
    )
    # A Version 2 gear's peg reaches into the barrel, so only the gear's own
    # band is checked; the peg is checked in test_version2_pegs_sit_inside_the_barrel.
    for got, want in zip(spans, _bands(asset_name)):
        if asset_name in V2_ASSET_NAMES:
            assert (got[0] if want[0] < 0 else got[1]) == pytest.approx(
                want[0] if want[0] < 0 else want[1], abs=BOUNDS_TOL_MM
            )
        else:
            assert got[0] == pytest.approx(want[0], abs=BOUNDS_TOL_MM)
            assert got[1] == pytest.approx(want[1], abs=BOUNDS_TOL_MM)


@pytest.mark.parametrize("asset_name", ALL_ASSET_NAMES)
def test_each_gear_has_24_teeth_at_the_reference_tip_radius(asset_name):
    """
    24 teeth on a 15.0000 degree pitch, tip radius 16.1093702290795 mm. A pair
    meshes at an axis distance of 32.0473 mm, so a wrong tooth count or a wrong
    tip radius would stop the rollers turning together.
    """
    mesh = _load(asset_name)

    for z_low, z_high in _bands(asset_name):
        # Inset a millimetre at each end so the flat end faces do not join the
        # tip band.
        assert _tooth_clusters(mesh.vertices, z_low + 1.0, z_high - 1.0) == TOOTH_COUNT

    radius = np.hypot(mesh.vertices[:, 0], mesh.vertices[:, 1])
    assert float(radius.max()) == pytest.approx(TIP_RADIUS_MM, abs=TIP_RADIUS_TOL_MM)


@pytest.mark.parametrize("asset_name", ALL_ASSET_NAMES)
def test_the_two_gears_share_one_clocking(asset_name):
    """
    Both gears of a set are clocked identically about the axis, which is what
    lets a pair mesh at the top and the bottom at the same time. Measured as the
    circular mean of tip-band angles modulo the 15 degree pitch.
    """
    mesh = _load(asset_name)
    pitch = 360.0 / TOOTH_COUNT

    phases = []
    for z_low, z_high in _bands(asset_name):
        in_band = mesh.vertices[
            (mesh.vertices[:, 2] > z_low + 1.0) & (mesh.vertices[:, 2] < z_high - 1.0)
        ]
        radius = np.hypot(in_band[:, 0], in_band[:, 1])
        tips = in_band[radius > (TIP_RADIUS_MM - TIP_BAND_DEPTH_MM)]
        angles = np.degrees(np.arctan2(tips[:, 1], tips[:, 0])) % 360.0
        scaled = np.radians((angles % pitch) * TOOTH_COUNT)
        mean = (
            math.degrees(math.atan2(np.sin(scaled).mean(), np.cos(scaled).mean()))
            / TOOTH_COUNT
        )
        phases.append(mean % pitch)

    assert phases[0] == pytest.approx(phases[1], abs=0.01)


def test_the_two_sets_are_different_gears():
    """
    A and B are not interchangeable: B's teeth are clocked to fall into A's gaps
    and its bore is smaller. Swapping them would stop the pair meshing.
    """
    a = _load("gears_a")
    b = _load("gears_b")
    assert a.volume != pytest.approx(b.volume, abs=1.0)
    a_bore = np.hypot(a.vertices[:, 0], a.vertices[:, 1]).min()
    b_bore = np.hypot(b.vertices[:, 0], b.vertices[:, 1]).min()
    assert a_bore > b_bore


def test_the_version2_sets_are_their_own_gears():
    """Four distinct source files and four distinct outputs: nothing was copied twice."""
    a = _load("v2_gears_a")
    b = _load("v2_gears_b")
    assert a.volume != pytest.approx(b.volume, abs=1.0)
    for v2_name, v1_name in (("v2_gears_a", "gears_a"), ("v2_gears_b", "gears_b")):
        assert _load(v2_name).volume != pytest.approx(_load(v1_name).volume, abs=1.0)


def test_version2_provenance_records_four_distinct_sources(provenance):
    """The v8 gears came as four files; a duplicated file was the mistake B1 guards against."""
    samples = provenance["v2_source_samples"]
    assert set(samples) == {"v2_gears_a.bin", "v2_gears_b.bin"}
    hashes = [s["sha256"] for entry in samples.values() for s in entry]
    assert len(hashes) == 4 and len(set(hashes)) == 4
    assert provenance["v2"]["z_shift_mm"] == V2_Z_SHIFT_MM


@pytest.mark.parametrize("asset_name", V2_ASSET_NAMES)
def test_version2_pegs_sit_inside_the_barrel(asset_name):
    """
    Each Version 2 gear carries a keyed peg 15 mm long that lies inside the
    barrel in this frame (z 0..15 from the bottom gear, 39..54 from the top),
    never wider than the widest key. The Version 1 set has no such geometry.
    """
    mesh = _load(asset_name)
    v = mesh.vertices
    r = np.hypot(v[:, 0], v[:, 1])
    # Above the pin band on the bottom gear; the top gear's peg hangs down from
    # the barrel's top face and its notch is cut into the gear body above it.
    lower = (v[:, 2] > V2_PIN_HEIGHT_MM + 0.5) & (v[:, 2] < V2_PEG_LENGTH_MM - 0.5)
    upper = (v[:, 2] > V2_BARREL_HEIGHT_MM - V2_PEG_LENGTH_MM + 0.5) & (
        v[:, 2] < V2_BARREL_HEIGHT_MM - 0.5
    )
    for inside in (lower, upper):
        assert inside.any(), "a peg is missing from the barrel"
        assert float(r[inside].max()) <= V2_PEG_MAX_RADIUS_MM
    pin = (v[:, 2] > 0.5) & (v[:, 2] < V2_PIN_HEIGHT_MM - 0.5)
    assert pin.any(), "the anti-rotation pin is missing"
    assert float(r[pin].max()) <= V2_PIN_MAX_RADIUS_MM
    assert float(v[lower | upper][:, 2].max()) <= V2_BARREL_HEIGHT_MM
    assert not (
        (_load("gears_a").vertices[:, 2] > 0.5)
        & (_load("gears_a").vertices[:, 2] < 51.5)
    ).any()


if __name__ == "__main__":
    regenerate()
