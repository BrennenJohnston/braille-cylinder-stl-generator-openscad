import shutil
from pathlib import Path

import pytest
import trimesh

from tests.mesh_comparison import MeshComparator, _parse_cloudcompare_asc_distances


def _base_config(
    *,
    cloudcompare_enabled: bool = True,
    require_max_surface_deviation: bool = True,
    icp_enabled: bool = True,
) -> dict:
    return {
        "tolerances": {
            "volume": {"percent": 1.0},
            "surface_area": {"percent": 0.5},
            "bounding_box": {"mm": 0.1},
            "max_surface_deviation": {"mm": 0.05},
        },
        "required_checks": {
            "watertightness": {"required": True, "must_match": True},
            "volume": {"required": True},
            "surface_area": {"required": True},
            "bounding_box": {"required": True},
            "max_surface_deviation": {
                "required": require_max_surface_deviation,
                "skip_if_missing_tools": True,
            },
        },
        "alignment": {
            "icp": {
                "enabled": icp_enabled,
                "threshold_for_alignment_mm": 0.5,
                "max_rms_mm": 0.01,
            }
        },
        "cloudcompare": {
            "enabled": cloudcompare_enabled,
            "sampling_density": 1000,
            "max_runtime_seconds": 10,
            "c2m_both_directions": True,
        },
    }


def _write_box_stl(path: Path, *, translate_x: float = 0.0) -> None:
    mesh = trimesh.creation.box(extents=(10.0, 10.0, 2.0))
    if translate_x:
        mesh.apply_translation([translate_x, 0.0, 0.0])
    mesh.export(path)


def test_parse_cloudcompare_asc_distances(tmp_path: Path):
    asc = tmp_path / "cloud.asc"
    asc.write_text(
        "X,Y,Z,Distance\n0,0,0,0.1\n1,0,0,0.2\n2,0,0,0.3\n",
        encoding="utf-8",
    )

    max_d, mean_d, count = _parse_cloudcompare_asc_distances(asc, separator=",")
    assert count == 3
    assert max_d == pytest.approx(0.3)
    assert mean_d == pytest.approx((0.1 + 0.2 + 0.3) / 3.0)


def test_max_surface_deviation_required_skips_if_cloudcompare_missing(tmp_path: Path):
    ref = tmp_path / "ref.stl"
    test = tmp_path / "test.stl"
    _write_box_stl(ref)
    shutil.copy2(ref, test)

    comparator = MeshComparator(_base_config(cloudcompare_enabled=True))
    # Ensure we simulate "missing tool"
    comparator.cloudcompare_path = None

    result = comparator.compare(ref, test)
    assert result.passed is True
    assert result.cloudcompare_available is False
    assert result.max_surface_deviation_mm is None


def test_max_surface_deviation_enforced_when_required_and_computed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    ref = tmp_path / "ref.stl"
    test = tmp_path / "test.stl"
    _write_box_stl(ref)
    shutil.copy2(ref, test)

    comparator = MeshComparator(_base_config(cloudcompare_enabled=True))
    comparator.cloudcompare_path = Path("CloudCompare")  # pretend it's installed

    def fake_compute_surface_deviation(self, reference_stl, test_stl, work_dir=None):
        return 0.123, 0.05

    monkeypatch.setattr(
        MeshComparator, "_compute_surface_deviation", fake_compute_surface_deviation
    )

    result = comparator.compare(ref, test)
    assert result.passed is False
    assert any("Max surface deviation" in f for f in result.failures)


def test_icp_alignment_triggered_and_reloads_properties(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    ref = tmp_path / "ref.stl"
    test = tmp_path / "test_translated.stl"
    _write_box_stl(ref)
    _write_box_stl(test, translate_x=5.0)  # exceeds 0.5mm ICP threshold

    comparator = MeshComparator(
        _base_config(cloudcompare_enabled=True, icp_enabled=True)
    )
    comparator.cloudcompare_path = Path("CloudCompare")  # pretend it's installed

    def fake_icp(self, data_mesh: Path, model_mesh: Path, work_dir: Path):
        work_dir.mkdir(parents=True, exist_ok=True)
        aligned = work_dir / "aligned.stl"
        shutil.copy2(model_mesh, aligned)  # perfect alignment for test
        return aligned, 0.001

    def fake_compute_surface_deviation(self, reference_stl, test_stl, work_dir=None):
        return 0.0, 0.0

    monkeypatch.setattr(MeshComparator, "_cloudcompare_icp_align_mesh", fake_icp)
    monkeypatch.setattr(
        MeshComparator, "_compute_surface_deviation", fake_compute_surface_deviation
    )

    result = comparator.compare(ref, test)
    assert result.passed is True
    assert result.icp_performed is True
    assert result.icp_rms_mm == pytest.approx(0.001)
