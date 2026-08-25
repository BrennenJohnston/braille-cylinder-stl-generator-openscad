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

# Where the derived binaries live. Only regenerate() needs this; the tests read
# this repo's own STLs and its provenance file, so the suite passes on a machine
# that does not have the web repo checked out.
WEB_REPO = Path(r"C:\Users\WATAP\Documents\github\braille-cylinder-stl-generator")
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
BOUNDS_TOL_MM = 0.001
XY_LIMIT_MM = 16.110


def _read_packed(path):
    """Read one of the web repo's .bin assets into (vertices, faces)."""
    data = path.read_bytes()
    if data[:6] != GEAR_MAGIC:
        raise ValueError(f"{path.name}: bad magic {data[:6]!r}, expected {GEAR_MAGIC!r}")
    vert_count, tri_count = struct.unpack_from("<II", data, 6)
    vertices = np.frombuffer(data, dtype="<f4", count=3 * vert_count, offset=GEAR_HEADER_BYTES)
    faces = np.frombuffer(
        data, dtype="<u4", count=3 * tri_count, offset=GEAR_HEADER_BYTES + 12 * vert_count
    )
    return (
        vertices.reshape(-1, 3).astype(np.float64),
        faces.reshape(-1, 3).astype(np.int64),
    )


def regenerate():
    """Convert the web repo's .bin assets into this repo's frame as binary STLs."""
    import trimesh

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
        "assets": {},
    }

    web_manifest = json.loads((WEB_ASSETS_DIR / "gears_manifest.json").read_text(encoding="utf-8"))
    provenance["source_samples"] = {
        name: entry["sources"] for name, entry in web_manifest["assets"].items()
    }

    for asset_name in ASSET_NAMES:
        source = WEB_ASSETS_DIR / f"{asset_name}.bin"
        payload = source.read_bytes()
        vertices, faces = _read_packed(source)
        vertices[:, 2] += Z_SHIFT_MM

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

    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {PROVENANCE_PATH}")


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
        pytest.fail(f"{path} is missing. Regenerate with: python -m tests.test_gear_assets")
    payload = path.read_bytes()
    if payload.startswith(LFS_POINTER_PREFIX):
        pytest.fail(
            f"{path} is a Git LFS pointer, not the mesh. Run: git lfs pull"
        )
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


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
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


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
def test_asset_sits_in_this_repo_frame(asset_name):
    """Barrel base at z=0 means gears at z -10..0 and 52..62, axis at the origin."""
    mesh = _load(asset_name)
    low, high = mesh.bounds

    assert low[2] == pytest.approx(EXPECTED_Z_BANDS[0][0], abs=BOUNDS_TOL_MM)
    assert high[2] == pytest.approx(EXPECTED_Z_BANDS[1][1], abs=BOUNDS_TOL_MM)

    for axis in (0, 1):
        assert low[axis] >= -XY_LIMIT_MM
        assert high[axis] <= XY_LIMIT_MM


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
def test_asset_is_two_watertight_gears(asset_name):
    """One gear for each end of the barrel, each a closed solid."""
    mesh = _load(asset_name)
    mesh.merge_vertices()
    bodies = mesh.split(only_watertight=False)

    assert len(bodies) == 2
    assert all(body.is_watertight for body in bodies)
    assert all(body.volume > 0 for body in bodies)

    spans = sorted(
        (round(float(b.bounds[0][2]), 3), round(float(b.bounds[1][2]), 3)) for b in bodies
    )
    for got, want in zip(spans, EXPECTED_Z_BANDS):
        assert got[0] == pytest.approx(want[0], abs=BOUNDS_TOL_MM)
        assert got[1] == pytest.approx(want[1], abs=BOUNDS_TOL_MM)


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
def test_each_gear_has_24_teeth_at_the_reference_tip_radius(asset_name):
    """
    24 teeth on a 15.0000 degree pitch, tip radius 16.1093702290795 mm. A pair
    meshes at an axis distance of 32.0473 mm, so a wrong tooth count or a wrong
    tip radius would stop the rollers turning together.
    """
    mesh = _load(asset_name)

    for z_low, z_high in EXPECTED_Z_BANDS:
        # Inset a millimetre at each end so the flat end faces do not join the
        # tip band.
        assert _tooth_clusters(mesh.vertices, z_low + 1.0, z_high - 1.0) == TOOTH_COUNT

    radius = np.hypot(mesh.vertices[:, 0], mesh.vertices[:, 1])
    assert float(radius.max()) == pytest.approx(TIP_RADIUS_MM, abs=TIP_RADIUS_TOL_MM)


@pytest.mark.parametrize("asset_name", ASSET_NAMES)
def test_the_two_gears_share_one_clocking(asset_name):
    """
    Both gears of a set are clocked identically about the axis, which is what
    lets a pair mesh at the top and the bottom at the same time. Measured as the
    circular mean of tip-band angles modulo the 15 degree pitch.
    """
    mesh = _load(asset_name)
    pitch = 360.0 / TOOTH_COUNT

    phases = []
    for z_low, z_high in EXPECTED_Z_BANDS:
        in_band = mesh.vertices[
            (mesh.vertices[:, 2] > z_low + 1.0) & (mesh.vertices[:, 2] < z_high - 1.0)
        ]
        radius = np.hypot(in_band[:, 0], in_band[:, 1])
        tips = in_band[radius > (TIP_RADIUS_MM - TIP_BAND_DEPTH_MM)]
        angles = np.degrees(np.arctan2(tips[:, 1], tips[:, 0])) % 360.0
        scaled = np.radians((angles % pitch) * TOOTH_COUNT)
        mean = math.degrees(math.atan2(np.sin(scaled).mean(), np.cos(scaled).mean())) / TOOTH_COUNT
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


if __name__ == "__main__":
    regenerate()
