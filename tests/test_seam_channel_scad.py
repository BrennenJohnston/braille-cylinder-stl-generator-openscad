"""
Slicer seam channel — the OpenSCAD side of the web app's 2026-09-20 feature.

Phase O0 of the OpenSCAD parity plan (2026-09-21) lays the baseline: the four
default plates (Version 1 and Version 2, embossing and counter) were rendered
BEFORE the channel existed and their geometry signatures recorded in
``tests/fixtures/seam_channel/hashes.json``. From phase O1 on, a render with
``seam_channel = "Off"`` must reproduce that geometry exactly - the same
"off is identical" contract the web app pins with its
``tests/e2e/fixtures/*_before_seam_channel.stl``. Today the variable does not
exist yet, so ``-D seam_channel="Off"`` is inert and the test proves only that
the baseline is what the files render right now.

Why a signature and not STLs: the counter plates are 8 MB each as binary STL
(52 MB as ASCII) and the repo tracks ``*.stl`` through Git LFS. OpenSCAD
2026.01.03 renders the same command to the same bytes (checked twice on
2026-09-21), but a CHANGED command line flips the diagonal of a few coplanar
quads on the Version 2 countersink slivers - identical vertices, different
bytes - so the contract is the geometry signature (``_signature`` below), not
the file hash, and it fits in 3 KB.

Render tests skip when no OpenSCAD binary is available. Verdicts come from the
output text and file existence, never from an exit code.

License: PolyForm Noncommercial 1.0.0
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "seam_channel"
HASHES = FIXTURES / "hashes.json"

sys.path.insert(0, str(Path(__file__).parent))

from test_text_too_long import _resolve_openscad_path  # noqa: E402  (shared helper)


@pytest.fixture(scope="module")
def openscad_binary():
    """The console wrapper, driven directly, so output text can be judged."""
    resolved = _resolve_openscad_path()
    candidates = []
    if resolved is not None:
        candidates.append(Path(str(resolved).replace(".exe", ".com")))
        candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    pytest.skip("OpenSCAD not available for the seam channel render tests")


@pytest.fixture(scope="module")
def baseline():
    return json.loads(HASHES.read_text(encoding="utf-8"))


# The flag set every baseline render was made with. It is part of the byte
# contract: with --check-parameter-ranges=true OpenSCAD triangulates a few
# coplanar quads on the Version 2 countersink slivers with the other diagonal
# (same vertices, different bytes), so a render without it does not match.
BASELINE_FLAGS = [
    "--hardwarnings",
    "--check-parameter-ranges=true",
    "--export-format",
    "binstl",
]


def _signature(data):
    """
    The geometry of a binary STL, independent of how its quads were split.

    OpenSCAD 2026.01.03 renders identical vertices from run to run, but on a
    few coplanar quads (the Version 2 countersink slivers) it picks the other
    diagonal whenever the command line changes - same shape, different bytes.
    Triangle count, the unique vertex cloud, volume and area do not move under
    a diagonal flip, so they are what the baseline pins.
    """
    import struct

    import numpy as np

    count = struct.unpack_from("<I", data, 80)[0]
    dtype = np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")])
    tris = np.frombuffer(data, dtype=dtype, count=count, offset=84)["v"].astype(
        np.float64
    )
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    volume = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    area = float((np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2.0).sum())
    points = np.unique(np.round(tris.reshape(-1, 3), 5), axis=0)
    return {
        "tri_count": int(count),
        "unique_vertex_count": int(len(points)),
        "vertex_sha256": hashlib.sha256(points.tobytes()).hexdigest(),
        "volume_mm3": round(volume, 6),
        "area_mm2": round(area, 6),
    }


def _render(binary, scad_file, stl_path, defines, flags=BASELINE_FLAGS):
    """Render once as binary STL. Returns the combined stdout+stderr."""
    command = [str(binary), *flags]
    for key, value in defines.items():
        command += [
            "-D",
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}",
        ]
    command += ["-o", str(stl_path), str(scad_file)]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT
    )
    return (result.stdout or "") + "\n" + (result.stderr or "")


def test_baseline_records_the_four_default_plates(baseline):
    """The hash file names both files, both plates, and the binary export."""
    renders = baseline["renders"]
    assert set(renders) == {"v1_emboss", "v1_counter", "v2_emboss", "v2_counter"}
    for name, record in renders.items():
        assert (PROJECT_ROOT / record["file"]).is_file(), name
        assert record["flags"] == BASELINE_FLAGS, name
        assert record["defines"]["seam_channel"] == "Off", name
        assert len(record["vertex_sha256"]) == 64
        assert record["tri_count"] > 0 and record["unique_vertex_count"] > 0
        assert record["volume_mm3"] > 0 and record["area_mm2"] > 0
        assert record["byte_size"] == 84 + 50 * record["tri_count"]
        assert record["warnings_or_errors"] == 0


@pytest.mark.slow
@pytest.mark.parametrize("name", ["v1_emboss", "v1_counter", "v2_emboss", "v2_counter"])
def test_seam_channel_off_reproduces_the_pre_channel_bytes(
    openscad_binary, baseline, tmp_path, name
):
    """
    ``seam_channel = "Off"`` renders the exact bytes the file produced before
    the channel existed. Until phase O1 lands the define is inert, so this is
    the baseline proving itself; afterwards it is the off-state contract.
    """
    record = baseline["renders"][name]
    stl_path = tmp_path / f"{name}.stl"
    output = _render(
        openscad_binary,
        PROJECT_ROOT / record["file"],
        stl_path,
        dict(record["defines"]),
    )
    assert "ERROR:" not in output, f"OpenSCAD reported an error:\n{output[:800]}"
    assert "WARNING:" not in output, f"OpenSCAD reported a warning:\n{output[:800]}"
    assert stl_path.exists(), f"no STL was written:\n{output[:800]}"
    data = stl_path.read_bytes()
    assert len(data) == record["byte_size"], (
        f"{name}: {len(data)} bytes, baseline {record['byte_size']}"
    )
    got = _signature(data)
    want = {key: record[key] for key in got}
    assert got == want, (
        f"{name}: the Off render drifted from the baseline geometry:\n{got}\n{want}"
    )
