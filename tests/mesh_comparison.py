"""
Mesh Comparison Module for Cross-Platform STL Validation

This module provides mesh comparison capabilities using:
1. trimesh for property-based comparison (volume, area, bbox, watertightness)
2. CloudCompare CLI for optional numeric surface deviation (Hausdorff-like distance)

License: PolyForm Noncommercial 1.0.0
"""

import json
import logging
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import trimesh

logger = logging.getLogger(__name__)


def _parse_cloudcompare_asc_distances(
    asc_path: Path, separator: str = ","
) -> Tuple[float, float, int]:
    """
    Parse a CloudCompare ASCII cloud export (ASC) produced after a C2M_DIST run.

    We assume the *last* numeric column corresponds to the active scalar field
    (the C2M distance), which is CloudCompare's default behavior when exporting.

    Returns:
        (max_distance, mean_distance, count)

    Raises:
        ValueError: if no numeric distance values can be parsed.
    """
    distances: List[float] = []

    with open(asc_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            # Skip obvious headers/comments (CloudCompare may emit headers depending on flags)
            if line.startswith("#") or line.startswith("//"):
                continue

            parts = [p.strip() for p in line.split(separator)]
            if len(parts) < 4:
                # Need at least XYZ + one scalar field value
                continue

            try:
                floats = [float(p) for p in parts]
            except ValueError:
                # Likely a header line (e.g., "X,Y,Z,..." from -ADD_HEADER)
                continue

            distances.append(float(floats[-1]))

    if not distances:
        raise ValueError(f"No numeric distances parsed from {asc_path}")

    max_d = float(max(distances))
    mean_d = float(sum(distances) / len(distances))
    return max_d, mean_d, len(distances)


@dataclass
class MeshProperties:
    """Properties extracted from a mesh."""

    volume: float  # mm³
    surface_area: float  # mm²
    bounding_box: np.ndarray  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    face_count: int
    vertex_count: int
    is_watertight: bool
    centroid: np.ndarray  # [x, y, z]


@dataclass
class ComparisonResult:
    """Result of mesh comparison."""

    passed: bool
    reference_properties: MeshProperties
    test_properties: MeshProperties

    # Differences
    volume_diff_percent: float
    surface_area_diff_percent: float
    bounding_box_diff_mm: float
    face_count_diff: int
    vertex_count_diff: int
    watertightness_match: bool

    # Optional numeric deviation (CloudCompare)
    max_surface_deviation_mm: Optional[float] = None
    mean_surface_deviation_mm: Optional[float] = None
    cloudcompare_available: bool = False

    # ICP alignment info
    icp_performed: bool = False
    icp_rms_mm: Optional[float] = None

    # Failures
    failures: list = field(default_factory=list)

    # Metadata
    comparison_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "reference_properties": {
                "volume_mm3": self.reference_properties.volume,
                "surface_area_mm2": self.reference_properties.surface_area,
                "bounding_box_mm": self.reference_properties.bounding_box.tolist(),
                "face_count": self.reference_properties.face_count,
                "vertex_count": self.reference_properties.vertex_count,
                "is_watertight": self.reference_properties.is_watertight,
                "centroid_mm": self.reference_properties.centroid.tolist(),
            },
            "test_properties": {
                "volume_mm3": self.test_properties.volume,
                "surface_area_mm2": self.test_properties.surface_area,
                "bounding_box_mm": self.test_properties.bounding_box.tolist(),
                "face_count": self.test_properties.face_count,
                "vertex_count": self.test_properties.vertex_count,
                "is_watertight": self.test_properties.is_watertight,
                "centroid_mm": self.test_properties.centroid.tolist(),
            },
            "differences": {
                "volume_diff_percent": self.volume_diff_percent,
                "surface_area_diff_percent": self.surface_area_diff_percent,
                "bounding_box_diff_mm": self.bounding_box_diff_mm,
                "face_count_diff": self.face_count_diff,
                "vertex_count_diff": self.vertex_count_diff,
                "watertightness_match": self.watertightness_match,
            },
            "numeric_deviation": {
                "max_surface_deviation_mm": self.max_surface_deviation_mm,
                "mean_surface_deviation_mm": self.mean_surface_deviation_mm,
                "cloudcompare_available": self.cloudcompare_available,
            },
            "alignment": {
                "icp_performed": self.icp_performed,
                "icp_rms_mm": self.icp_rms_mm,
            },
            "failures": self.failures,
            "comparison_time_seconds": self.comparison_time_seconds,
        }


class MeshComparator:
    """
    Compare two STL meshes using multiple metrics.

    Provides:
    - Property-based comparison (trimesh)
    - Optional numeric deviation (CloudCompare CLI)
    - Optional ICP alignment before comparison
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mesh comparator with configuration.

        Args:
            config: Configuration dict (from tests/compare_config.json)
        """
        self.config = config
        self.tolerances = config["tolerances"]
        self.required_checks = config["required_checks"]
        self.alignment_config = config["alignment"]
        self.cloudcompare_config = config.get("cloudcompare", {})

        # Try to find CloudCompare (optional)
        self.cloudcompare_path = self._find_cloudcompare()
        if self.cloudcompare_path:
            logger.info(f"CloudCompare found: {self.cloudcompare_path}")
        else:
            logger.warning(
                "CloudCompare not found - numeric deviation checks will be skipped"
            )

    def _find_cloudcompare(self) -> Optional[Path]:
        """Find CloudCompare executable (optional)."""
        # Check if in PATH
        cc_cmd = shutil.which("CloudCompare")
        if cc_cmd:
            return Path(cc_cmd)

        # Platform-specific paths
        system = platform.system()
        if system == "Windows":
            paths = [
                Path(r"C:\Program Files\CloudCompare\CloudCompare.exe"),
            ]
        elif system == "Darwin":
            paths = [
                Path("/Applications/CloudCompare.app/Contents/MacOS/CloudCompare"),
            ]
        elif system == "Linux":
            paths = [
                Path("/snap/bin/cloudcompare"),
                Path("/usr/bin/cloudcompare"),
                Path("/usr/local/bin/cloudcompare"),
            ]
        else:
            paths = []

        for path in paths:
            if path.exists():
                return path

        return None

    def _cloudcompare_is_enabled(self) -> bool:
        """Whether CloudCompare usage is enabled by config."""
        return bool(self.cloudcompare_config.get("enabled", True))

    def _cloudcompare_timeout_seconds(self) -> int:
        """Max runtime per CloudCompare invocation."""
        return int(self.cloudcompare_config.get("max_runtime_seconds", 120))

    def _cloudcompare_sampling_points(self) -> int:
        """Number of points to sample from each mesh surface for C2M distance."""
        return int(self.cloudcompare_config.get("sampling_density", 10000))

    def _run_cloudcompare(
        self, args: List[str], cwd: Path, timeout_seconds: int
    ) -> subprocess.CompletedProcess:
        """
        Run CloudCompare CLI and capture stdout/stderr.

        Args:
            args: CloudCompare CLI args (without the executable)
            cwd: Working directory (used to keep any auto-generated files contained)
            timeout_seconds: Timeout for the CloudCompare process
        """
        if not self.cloudcompare_path:
            raise RuntimeError("CloudCompare not available")

        # On Windows, CloudCompare is a GUI app; CREATE_NO_WINDOW prevents flashing a console window.
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        cmd = [str(self.cloudcompare_path), "-SILENT", "-AUTO_SAVE", "OFF", *args]
        logger.debug("CloudCompare cmd: %s (cwd=%s)", " ".join(cmd), cwd)

        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            creationflags=creationflags,
        )

    def _parse_icp_rms_mm(self, text: str) -> Optional[float]:
        """Best-effort extraction of ICP RMS value from CloudCompare output/log text."""
        # Examples we may see: "RMS: 0.00123" / "RMS error = 1e-4"
        match = re.search(
            r"\bRMS(?:\s+error)?\b[^0-9eE+\-]*([0-9]*\.?[0-9]+(?:[eE][+\-]?\d+)?)",
            text,
        )
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _cloudcompare_icp_align_mesh(
        self, data_mesh: Path, model_mesh: Path, work_dir: Path
    ) -> Tuple[Path, Optional[float]]:
        """
        Align 'data_mesh' to 'model_mesh' using CloudCompare ICP.

        Returns:
            (aligned_data_mesh_path, icp_rms_mm)
        """
        if not self.cloudcompare_path:
            raise RuntimeError("CloudCompare not available")

        work_dir.mkdir(parents=True, exist_ok=True)

        # Copy inputs to isolate any auto-generated outputs (e.g., transformation matrix files)
        data_copy = work_dir / "data.stl"
        model_copy = work_dir / "model.stl"
        shutil.copy2(data_mesh, data_copy)
        shutil.copy2(model_mesh, model_copy)

        aligned_path = work_dir / "data_aligned.stl"
        timeout = self._cloudcompare_timeout_seconds()

        icp_cfg = self.alignment_config.get("icp", {})
        # Keep defaults unless we explicitly set a few safe options.
        icp_args: List[str] = [
            "-M_EXPORT_FMT",
            "STL",
            "-O",
            data_copy.name,
            "-O",
            model_copy.name,
            "-ICP",
        ]

        # Optional knobs (CloudCompare accepts these in command line mode)
        overlap = icp_cfg.get("overlap_percent")
        if overlap is not None:
            icp_args.extend(["-OVERLAP", str(int(overlap))])

        # Remove the (unchanged) model mesh so we can save only the aligned data mesh
        icp_args.extend(
            [
                "-POP_MESHES",
                "-SAVE_MESHES",
                "FILE",
                aligned_path.name,
            ]
        )

        result = self._run_cloudcompare(icp_args, cwd=work_dir, timeout_seconds=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                "CloudCompare ICP failed:\n"
                f"  returncode={result.returncode}\n"
                f"  stdout={result.stdout}\n"
                f"  stderr={result.stderr}"
            )

        if not aligned_path.exists():
            raise RuntimeError(
                f"CloudCompare ICP did not produce aligned mesh: {aligned_path}"
            )

        # Best-effort RMS parsing (stdout/stderr, then any text outputs)
        rms = self._parse_icp_rms_mm(
            (result.stdout or "") + "\n" + (result.stderr or "")
        )
        if rms is None:
            for txt in sorted(work_dir.glob("*.txt")):
                try:
                    rms = self._parse_icp_rms_mm(
                        txt.read_text(encoding="utf-8", errors="ignore")
                    )
                except Exception:
                    continue
                if rms is not None:
                    break

        return aligned_path, rms

    def _cloudcompare_c2m_distance_stats(
        self, compared_mesh: Path, reference_mesh: Path, work_dir: Path
    ) -> Tuple[float, float]:
        """
        Compute cloud-to-mesh distance stats (max, mean) using CloudCompare.

        This will:
        - load compared_mesh (as mesh)
        - sample it to a point cloud (POINTS = sampling_density)
        - clear meshes, then load reference_mesh (as mesh)
        - run C2M_DIST (unsigned)
        - save the resulting cloud as ASCII (ASC) and compute max/mean from its scalar field
        """
        if not self.cloudcompare_path:
            raise RuntimeError("CloudCompare not available")

        work_dir.mkdir(parents=True, exist_ok=True)

        # Copy inputs into work_dir so any side files stay contained
        compared_copy = work_dir / "compared.stl"
        reference_copy = work_dir / "reference.stl"
        shutil.copy2(compared_mesh, compared_copy)
        shutil.copy2(reference_mesh, reference_copy)

        out_cloud = work_dir / "c2m_result.asc"
        timeout = self._cloudcompare_timeout_seconds()
        n_points = self._cloudcompare_sampling_points()

        cc_args: List[str] = [
            "-C_EXPORT_FMT",
            "ASC",
            "-PREC",
            "12",
            "-SEP",
            "COMMA",
            "-ADD_HEADER",
            "-O",
            compared_copy.name,
            "-SAMPLE_MESH",
            "POINTS",
            str(n_points),
            "-CLEAR_MESHES",
            "-O",
            reference_copy.name,
            "-C2M_DIST",
            "-UNSIGNED",
            "-SAVE_CLOUDS",
            "FILE",
            out_cloud.name,
        ]

        result = self._run_cloudcompare(cc_args, cwd=work_dir, timeout_seconds=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                "CloudCompare C2M_DIST failed:\n"
                f"  returncode={result.returncode}\n"
                f"  stdout={result.stdout}\n"
                f"  stderr={result.stderr}"
            )

        if not out_cloud.exists():
            raise RuntimeError(
                f"CloudCompare did not produce expected output cloud: {out_cloud}"
            )

        max_d, mean_d, _count = _parse_cloudcompare_asc_distances(
            out_cloud, separator=","
        )
        return max_d, mean_d

    def load_mesh(self, stl_path: Path) -> trimesh.Trimesh:
        """
        Load STL file as trimesh.

        Args:
            stl_path: Path to STL file

        Returns:
            Loaded mesh

        Raises:
            FileNotFoundError: If STL file doesn't exist
            ValueError: If STL file is invalid
        """
        if not stl_path.exists():
            raise FileNotFoundError(f"STL file not found: {stl_path}")

        try:
            mesh = trimesh.load(stl_path, force="mesh")
            logger.debug(
                f"Loaded mesh: {mesh.faces.shape[0]} faces, "
                f"{mesh.vertices.shape[0]} vertices"
            )
            return mesh
        except Exception as e:
            raise ValueError(f"Failed to load STL {stl_path}: {e}")

    def extract_properties(self, mesh: trimesh.Trimesh) -> MeshProperties:
        """
        Extract properties from mesh.

        Args:
            mesh: trimesh mesh

        Returns:
            MeshProperties with extracted data
        """
        return MeshProperties(
            volume=float(mesh.volume),
            surface_area=float(mesh.area),
            bounding_box=mesh.bounds,
            face_count=len(mesh.faces),
            vertex_count=len(mesh.vertices),
            is_watertight=mesh.is_watertight,
            centroid=mesh.centroid,
        )

    def compare(self, reference_stl: Path, test_stl: Path) -> ComparisonResult:
        """
        Compare two STL files.

        Args:
            reference_stl: Path to reference STL (web generator)
            test_stl: Path to test STL (OpenSCAD)

        Returns:
            ComparisonResult with all metrics
        """
        import time

        start_time = time.time()

        # Load meshes
        ref_mesh = self.load_mesh(reference_stl)
        test_mesh = self.load_mesh(test_stl)

        # Extract properties
        ref_props = self.extract_properties(ref_mesh)
        test_props = self.extract_properties(test_mesh)

        cloudcompare_available = self.cloudcompare_path is not None
        cloudcompare_enabled = (
            cloudcompare_available and self._cloudcompare_is_enabled()
        )

        # Optional: ICP alignment (CloudCompare)
        icp_performed = False
        icp_rms = None
        aligned_test_stl = test_stl

        # Numeric deviation (CloudCompare)
        max_deviation = None
        mean_deviation = None

        cc_tmp = None
        cc_root: Optional[Path] = None
        if cloudcompare_enabled:
            cc_tmp = tempfile.TemporaryDirectory(prefix="cloudcompare_")
            cc_root = Path(cc_tmp.name)

        try:
            # Decide whether to run ICP alignment (based on centroid distance heuristic)
            icp_cfg = self.alignment_config.get("icp", {})
            icp_enabled = bool(icp_cfg.get("enabled", False))
            icp_threshold = float(icp_cfg.get("threshold_for_alignment_mm", 0.0))

            centroid_distance = float(
                np.linalg.norm(ref_props.centroid - test_props.centroid)
            )

            if (
                cloudcompare_enabled
                and icp_enabled
                and centroid_distance > icp_threshold
            ):
                logger.info(
                    f"Centroid distance {centroid_distance:.3f}mm > {icp_threshold}mm; "
                    f"running ICP alignment with CloudCompare"
                )
                try:
                    aligned_test_stl, icp_rms = self._cloudcompare_icp_align_mesh(
                        data_mesh=test_stl,
                        model_mesh=reference_stl,
                        work_dir=cc_root / "icp",
                    )
                    icp_performed = True

                    # Reload aligned mesh for subsequent (translation-sensitive) checks
                    test_mesh = self.load_mesh(aligned_test_stl)
                    test_props = self.extract_properties(test_mesh)
                except Exception as e:
                    logger.warning(f"CloudCompare ICP alignment failed: {e}")

            # Calculate differences (after optional alignment)
            volume_diff_pct = (
                abs(ref_props.volume - test_props.volume) / ref_props.volume * 100.0
                if ref_props.volume > 0
                else 0.0
            )

            area_diff_pct = (
                abs(ref_props.surface_area - test_props.surface_area)
                / ref_props.surface_area
                * 100.0
                if ref_props.surface_area > 0
                else 0.0
            )

            # Bounding-box comparison needs to be robust to translation and rotation around the cylinder axis.
            # For this repo's current scope (cylinder-only), both generators emit cylinders aligned to Z
            # (they may differ by translation along Z). So we use Z-height + max radial diameter in XY:
            # - height_extent: max(z) - min(z)
            # - diameter_extent: 2 * max(sqrt(x^2 + y^2))
            def _cylinder_size_metrics_z(mesh: trimesh.Trimesh) -> tuple[float, float]:
                verts = mesh.vertices.astype(float)
                if verts.shape[0] == 0:
                    return 0.0, 0.0
                z = verts[:, 2]
                height_extent = float(z.max() - z.min())
                r = np.sqrt(verts[:, 0] ** 2 + verts[:, 1] ** 2)
                diameter_extent = float(2.0 * r.max())
                return height_extent, diameter_extent

            ref_h, ref_d = _cylinder_size_metrics_z(ref_mesh)
            test_h, test_d = _cylinder_size_metrics_z(test_mesh)
            bbox_diff = float(max(abs(ref_h - test_h), abs(ref_d - test_d)))

            face_diff = abs(ref_props.face_count - test_props.face_count)
            vertex_diff = abs(ref_props.vertex_count - test_props.vertex_count)
            watertight_match = ref_props.is_watertight == test_props.is_watertight

            # CloudCompare numeric deviation (optional tool, but can be required by config)
            if cloudcompare_enabled:
                try:
                    max_deviation, mean_deviation = self._compute_surface_deviation(
                        reference_stl, aligned_test_stl, work_dir=cc_root
                    )
                except Exception as e:
                    logger.warning(
                        f"CloudCompare surface deviation computation failed: {e}"
                    )

            # Check against tolerances
            failures = []

            # Volume check
            if self.required_checks["volume"]["required"]:
                vol_tol = self.tolerances["volume"]["percent"]
                if volume_diff_pct > vol_tol:
                    failures.append(
                        f"Volume difference {volume_diff_pct:.2f}% exceeds "
                        f"tolerance {vol_tol}%"
                    )

            # Surface area check
            if self.required_checks["surface_area"]["required"]:
                area_tol = self.tolerances["surface_area"]["percent"]
                if area_diff_pct > area_tol:
                    failures.append(
                        f"Surface area difference {area_diff_pct:.2f}% exceeds "
                        f"tolerance {area_tol}%"
                    )

            # Bounding box check
            if self.required_checks["bounding_box"]["required"]:
                bbox_tol = self.tolerances["bounding_box"]["mm"]
                if bbox_diff > bbox_tol:
                    failures.append(
                        f"Bounding box difference {bbox_diff:.3f}mm exceeds "
                        f"tolerance {bbox_tol}mm"
                    )

            # Watertightness check
            if self.required_checks["watertightness"]["required"]:
                if not watertight_match:
                    failures.append(
                        f"Watertightness mismatch: ref={ref_props.is_watertight}, "
                        f"test={test_props.is_watertight}"
                    )
                if (
                    self.required_checks["watertightness"]["must_match"]
                    and not test_props.is_watertight
                ):
                    failures.append("Test mesh is not watertight (required)")

            # ICP RMS sanity check (if available)
            if icp_performed and icp_rms is not None:
                max_rms = icp_cfg.get("max_rms_mm")
                if max_rms is not None and icp_rms > float(max_rms):
                    failures.append(
                        f"ICP RMS {icp_rms:.4f}mm exceeds max_rms {float(max_rms):.4f}mm"
                    )

            # Numeric deviation check (CloudCompare)
            max_dev_cfg = self.required_checks.get("max_surface_deviation", {})
            dev_required = bool(max_dev_cfg.get("required", False))
            skip_if_missing = bool(max_dev_cfg.get("skip_if_missing_tools", False))

            if max_deviation is None:
                # Missing tool or computation failure
                if dev_required:
                    if not cloudcompare_enabled:
                        if not skip_if_missing:
                            failures.append(
                                "Max surface deviation check required but CloudCompare is not available/enabled"
                            )
                    else:
                        failures.append(
                            "Max surface deviation check required but could not be computed (CloudCompare error)"
                        )
            else:
                dev_tol = self.tolerances["max_surface_deviation"]["mm"]
                if max_deviation > dev_tol and dev_required:
                    failures.append(
                        f"Max surface deviation {max_deviation:.3f}mm exceeds "
                        f"tolerance {dev_tol}mm"
                    )

            passed = len(failures) == 0
            duration = time.time() - start_time

            return ComparisonResult(
                passed=passed,
                reference_properties=ref_props,
                test_properties=test_props,
                volume_diff_percent=volume_diff_pct,
                surface_area_diff_percent=area_diff_pct,
                bounding_box_diff_mm=float(bbox_diff),
                face_count_diff=face_diff,
                vertex_count_diff=vertex_diff,
                watertightness_match=watertight_match,
                max_surface_deviation_mm=max_deviation,
                mean_surface_deviation_mm=mean_deviation,
                cloudcompare_available=cloudcompare_available,
                icp_performed=icp_performed,
                icp_rms_mm=icp_rms,
                failures=failures,
                comparison_time_seconds=duration,
            )
        finally:
            if cc_tmp is not None:
                cc_tmp.cleanup()

    def _compute_surface_deviation(
        self,
        reference_stl: Path,
        test_stl: Path,
        work_dir: Optional[Path] = None,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Compute symmetric surface deviation using CloudCompare CLI (C2M distance).

        Strategy:
        - sample mesh A -> cloud A, compute C2M(A -> B)
        - sample mesh B -> cloud B, compute C2M(B -> A)
        - return max(maxA, maxB) and mean(meanA, meanB)

        Note: This computes a Hausdorff-like metric based on sampled points (not exact).
        """
        if not self.cloudcompare_path:
            raise RuntimeError("CloudCompare not available")

        if work_dir is None:
            with tempfile.TemporaryDirectory(prefix="cloudcompare_") as td:
                return self._compute_surface_deviation(
                    reference_stl=reference_stl,
                    test_stl=test_stl,
                    work_dir=Path(td),
                )

        both_directions = bool(
            self.cloudcompare_config.get("c2m_both_directions", True)
        )

        # Test -> Reference
        dir_a = work_dir / "c2m_test_to_ref"
        max_a, mean_a = self._cloudcompare_c2m_distance_stats(
            compared_mesh=test_stl,
            reference_mesh=reference_stl,
            work_dir=dir_a,
        )

        if not both_directions:
            return max_a, mean_a

        # Reference -> Test
        dir_b = work_dir / "c2m_ref_to_test"
        max_b, mean_b = self._cloudcompare_c2m_distance_stats(
            compared_mesh=reference_stl,
            reference_mesh=test_stl,
            work_dir=dir_b,
        )

        max_dev = max(max_a, max_b)
        mean_dev = (mean_a + mean_b) / 2.0
        return float(max_dev), float(mean_dev)


def main():
    """Example usage and testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare two STL meshes")
    parser.add_argument("reference", type=Path, help="Reference STL file")
    parser.add_argument("test", type=Path, help="Test STL file")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("tests/compare_config.json"),
        help="Comparison config JSON",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Output comparison result as JSON",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Load config
        with open(args.config) as f:
            config = json.load(f)

        # Create comparator
        comparator = MeshComparator(config)

        # Compare meshes
        logger.info(f"Comparing: {args.reference.name} vs {args.test.name}")
        result = comparator.compare(args.reference, args.test)

        # Print results
        print("\n" + "=" * 70)
        print("MESH COMPARISON RESULTS")
        print("=" * 70)
        print(f"Status: {'✓ PASS' if result.passed else '✗ FAIL'}")
        print(f"\nVolume difference: {result.volume_diff_percent:.2f}%")
        print(f"Surface area difference: {result.surface_area_diff_percent:.2f}%")
        print(f"Bounding box difference: {result.bounding_box_diff_mm:.3f} mm")
        print(f"Face count difference: {result.face_count_diff}")
        print(f"Vertex count difference: {result.vertex_count_diff}")
        print(f"Watertightness match: {'Yes' if result.watertightness_match else 'No'}")

        if result.max_surface_deviation_mm is not None:
            print(f"\nMax surface deviation: {result.max_surface_deviation_mm:.3f} mm")
            print(f"Mean surface deviation: {result.mean_surface_deviation_mm:.3f} mm")
        elif result.cloudcompare_available:
            print("\nNumeric deviation: Not computed (implementation pending)")
        else:
            print("\nNumeric deviation: Skipped (CloudCompare not available)")

        if result.failures:
            print("\nFailures:")
            for failure in result.failures:
                print(f"  - {failure}")

        print(f"\nComparison time: {result.comparison_time_seconds:.2f} seconds")
        print("=" * 70)

        # Save JSON output if requested
        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            logger.info(f"Results saved to: {args.output_json}")

        return 0 if result.passed else 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
