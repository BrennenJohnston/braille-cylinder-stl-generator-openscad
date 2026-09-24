"""
Visual STL Diff Tool

Generates visual comparisons between reference and test STL files for debugging
geometry discrepancies between OpenSCAD and web generator implementations.

Features:
- Side-by-side PNG renders
- Overlay comparison with difference highlighting
- Mesh statistics comparison table
- Optional deviation heatmap (requires CloudCompare)

Usage:
    python scripts/visual_stl_diff.py <reference.stl> <test.stl> [--output-dir artifacts/visual_diff]

    # Compare specific test case
    python scripts/visual_stl_diff.py tests/fixtures/cross_platform/cylinder_rounded_counter_indicators_on/reference.stl /tmp/openscad_output.stl

Requirements:
    pip install trimesh numpy matplotlib pillow

License: PolyForm Noncommercial 1.0.0
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np

try:
    import trimesh
except ImportError:
    print("Error: trimesh is required. Install with: pip install trimesh")
    sys.exit(1)

# Optional dependencies. Importing Normalize, Axes3D, and Image here is how
# availability is probed, so they are unused by design (F401).
try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize  # noqa: F401
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. PNG rendering disabled.")

try:
    from PIL import Image  # noqa: F401

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_mesh(stl_path: Path) -> trimesh.Trimesh:
    """Load STL file as trimesh object."""
    mesh = trimesh.load_mesh(str(stl_path), force="mesh")
    logger.info(
        f"Loaded {stl_path.name}: {len(mesh.faces)} faces, {len(mesh.vertices)} vertices"
    )
    return mesh


def compute_mesh_stats(mesh: trimesh.Trimesh) -> Dict:
    """Compute comprehensive mesh statistics."""
    bounds = mesh.bounds
    bbox_size = bounds[1] - bounds[0]

    return {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "volume_mm3": float(mesh.volume),
        "surface_area_mm2": float(mesh.area),
        "bbox_min": bounds[0].tolist(),
        "bbox_max": bounds[1].tolist(),
        "bbox_size_mm": bbox_size.tolist(),
        "centroid_mm": mesh.centroid.tolist(),
        "is_watertight": mesh.is_watertight,
    }


def compare_stats(ref_stats: Dict, test_stats: Dict) -> Dict:
    """Compare statistics between reference and test mesh."""
    volume_diff = abs(ref_stats["volume_mm3"] - test_stats["volume_mm3"])
    volume_pct = (
        (volume_diff / ref_stats["volume_mm3"] * 100)
        if ref_stats["volume_mm3"] > 0
        else 0
    )

    area_diff = abs(ref_stats["surface_area_mm2"] - test_stats["surface_area_mm2"])
    area_pct = (
        (area_diff / ref_stats["surface_area_mm2"] * 100)
        if ref_stats["surface_area_mm2"] > 0
        else 0
    )

    return {
        "volume_diff_mm3": volume_diff,
        "volume_diff_percent": volume_pct,
        "surface_area_diff_mm2": area_diff,
        "surface_area_diff_percent": area_pct,
        "vertex_diff": abs(ref_stats["vertices"] - test_stats["vertices"]),
        "face_diff": abs(ref_stats["faces"] - test_stats["faces"]),
        "watertight_match": ref_stats["is_watertight"] == test_stats["is_watertight"],
    }


def render_mesh_view(
    mesh: trimesh.Trimesh,
    title: str,
    output_path: Path,
    elev: float = 30,
    azim: float = 45,
    color: str = "steelblue",
):
    """Render mesh to PNG using matplotlib."""
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib not available, skipping render")
        return

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Plot mesh faces
    ax.plot_trisurf(
        mesh.vertices[:, 0],
        mesh.vertices[:, 1],
        mesh.vertices[:, 2],
        triangles=mesh.faces,
        color=color,
        alpha=0.8,
        edgecolor="none",
    )

    # Set equal aspect ratio
    bounds = mesh.bounds
    max_range = (bounds[1] - bounds[0]).max() / 2.0
    mid = (bounds[1] + bounds[0]) / 2.0
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title(title)
    ax.view_init(elev=elev, azim=azim)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved render: {output_path}")


def render_side_by_side(
    ref_mesh: trimesh.Trimesh,
    test_mesh: trimesh.Trimesh,
    output_path: Path,
    ref_name: str = "Reference",
    test_name: str = "Test",
):
    """Render reference and test meshes side by side."""
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib not available, skipping side-by-side render")
        return

    fig = plt.figure(figsize=(16, 8))

    for idx, (mesh, name, color) in enumerate(
        [(ref_mesh, ref_name, "steelblue"), (test_mesh, test_name, "coral")]
    ):
        ax = fig.add_subplot(1, 2, idx + 1, projection="3d")

        ax.plot_trisurf(
            mesh.vertices[:, 0],
            mesh.vertices[:, 1],
            mesh.vertices[:, 2],
            triangles=mesh.faces,
            color=color,
            alpha=0.8,
            edgecolor="none",
        )

        # Set equal aspect ratio
        bounds = mesh.bounds
        max_range = (bounds[1] - bounds[0]).max() / 2.0
        mid = (bounds[1] + bounds[0]) / 2.0
        ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
        ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
        ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title(f"{name}\n{len(mesh.faces)} faces, {len(mesh.vertices)} verts")
        ax.view_init(elev=30, azim=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved side-by-side: {output_path}")


def render_overlay(
    ref_mesh: trimesh.Trimesh, test_mesh: trimesh.Trimesh, output_path: Path
):
    """Render both meshes overlaid for visual comparison."""
    if not HAS_MATPLOTLIB:
        logger.warning("matplotlib not available, skipping overlay render")
        return

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection="3d")

    # Reference mesh in blue (semi-transparent)
    ax.plot_trisurf(
        ref_mesh.vertices[:, 0],
        ref_mesh.vertices[:, 1],
        ref_mesh.vertices[:, 2],
        triangles=ref_mesh.faces,
        color="steelblue",
        alpha=0.4,
        edgecolor="none",
        label="Reference",
    )

    # Test mesh in red (semi-transparent)
    ax.plot_trisurf(
        test_mesh.vertices[:, 0],
        test_mesh.vertices[:, 1],
        test_mesh.vertices[:, 2],
        triangles=test_mesh.faces,
        color="coral",
        alpha=0.4,
        edgecolor="none",
        label="Test",
    )

    # Set equal aspect ratio using combined bounds
    all_bounds = np.vstack([ref_mesh.bounds, test_mesh.bounds])
    bounds_min = all_bounds.min(axis=0)
    bounds_max = all_bounds.max(axis=0)
    max_range = (bounds_max - bounds_min).max() / 2.0
    mid = (bounds_max + bounds_min) / 2.0
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("Overlay Comparison\nBlue=Reference, Red=Test")
    ax.view_init(elev=30, azim=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved overlay: {output_path}")


def generate_stats_table(
    ref_stats: Dict, test_stats: Dict, comparison: Dict, output_path: Path
):
    """Generate HTML table of comparison statistics."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>STL Comparison Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4a90d9; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .pass {{ color: green; font-weight: bold; }}
        .fail {{ color: red; font-weight: bold; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>STL Visual Diff Report</h1>
    <p class="timestamp">Generated: {timestamp}</p>
    
    <h2>Mesh Statistics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Reference</th>
            <th>Test</th>
            <th>Difference</th>
        </tr>
        <tr>
            <td>Vertices</td>
            <td>{ref_verts}</td>
            <td>{test_verts}</td>
            <td>{vert_diff}</td>
        </tr>
        <tr>
            <td>Faces</td>
            <td>{ref_faces}</td>
            <td>{test_faces}</td>
            <td>{face_diff}</td>
        </tr>
        <tr>
            <td>Volume (mm³)</td>
            <td>{ref_vol:.3f}</td>
            <td>{test_vol:.3f}</td>
            <td class="{vol_class}">{vol_diff:.3f} ({vol_pct:.2f}%)</td>
        </tr>
        <tr>
            <td>Surface Area (mm²)</td>
            <td>{ref_area:.3f}</td>
            <td>{test_area:.3f}</td>
            <td class="{area_class}">{area_diff:.3f} ({area_pct:.2f}%)</td>
        </tr>
        <tr>
            <td>Watertight</td>
            <td>{ref_watertight}</td>
            <td>{test_watertight}</td>
            <td class="{water_class}">{water_match}</td>
        </tr>
    </table>
    
    <h2>Visual Comparison</h2>
    <p>See accompanying PNG files for visual renders.</p>
</body>
</html>
"""

    vol_class = "pass" if comparison["volume_diff_percent"] < 2.5 else "fail"
    area_class = "pass" if comparison["surface_area_diff_percent"] < 4.0 else "fail"
    water_class = "pass" if comparison["watertight_match"] else "fail"

    html = html.format(
        timestamp=datetime.now().isoformat(),
        ref_verts=ref_stats["vertices"],
        test_verts=test_stats["vertices"],
        vert_diff=comparison["vertex_diff"],
        ref_faces=ref_stats["faces"],
        test_faces=test_stats["faces"],
        face_diff=comparison["face_diff"],
        ref_vol=ref_stats["volume_mm3"],
        test_vol=test_stats["volume_mm3"],
        vol_diff=comparison["volume_diff_mm3"],
        vol_pct=comparison["volume_diff_percent"],
        vol_class=vol_class,
        ref_area=ref_stats["surface_area_mm2"],
        test_area=test_stats["surface_area_mm2"],
        area_diff=comparison["surface_area_diff_mm2"],
        area_pct=comparison["surface_area_diff_percent"],
        area_class=area_class,
        ref_watertight="Yes" if ref_stats["is_watertight"] else "No",
        test_watertight="Yes" if test_stats["is_watertight"] else "No",
        water_match="Match" if comparison["watertight_match"] else "MISMATCH",
        water_class=water_class,
    )

    with open(output_path, "w") as f:
        f.write(html)
    logger.info(f"Saved report: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate visual comparison between reference and test STL files"
    )
    parser.add_argument("reference_stl", type=Path, help="Reference STL file path")
    parser.add_argument("test_stl", type=Path, help="Test STL file path")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("artifacts/visual_diff"),
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help="Name for this comparison (defaults to reference filename)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate inputs
    if not args.reference_stl.exists():
        logger.error(f"Reference file not found: {args.reference_stl}")
        sys.exit(1)
    if not args.test_stl.exists():
        logger.error(f"Test file not found: {args.test_stl}")
        sys.exit(1)

    # Determine comparison name
    name = args.name or args.reference_stl.parent.name

    # Create output directory
    output_dir = args.output_dir / name
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Load meshes
    logger.info("Loading meshes...")
    ref_mesh = load_mesh(args.reference_stl)
    test_mesh = load_mesh(args.test_stl)

    # Compute statistics
    logger.info("Computing statistics...")
    ref_stats = compute_mesh_stats(ref_mesh)
    test_stats = compute_mesh_stats(test_mesh)
    comparison = compare_stats(ref_stats, test_stats)

    # Save statistics JSON
    stats_data = {
        "reference": ref_stats,
        "test": test_stats,
        "comparison": comparison,
        "files": {
            "reference": str(args.reference_stl),
            "test": str(args.test_stl),
        },
        "generated_at": datetime.now().isoformat(),
    }
    with open(output_dir / "comparison_stats.json", "w") as f:
        json.dump(stats_data, f, indent=2)

    # Generate renders
    if HAS_MATPLOTLIB:
        logger.info("Generating renders...")
        render_mesh_view(
            ref_mesh, "Reference (Web Generator)", output_dir / "reference.png"
        )
        render_mesh_view(
            test_mesh, "Test (OpenSCAD)", output_dir / "test.png", color="coral"
        )
        render_side_by_side(
            ref_mesh,
            test_mesh,
            output_dir / "side_by_side.png",
            ref_name="Reference (Web)",
            test_name="Test (OpenSCAD)",
        )
        render_overlay(ref_mesh, test_mesh, output_dir / "overlay.png")

    # Generate HTML report
    generate_stats_table(ref_stats, test_stats, comparison, output_dir / "report.html")

    # Print summary
    print("\n" + "=" * 60)
    print("VISUAL DIFF SUMMARY")
    print("=" * 60)
    print(f"Reference: {args.reference_stl}")
    print(f"Test: {args.test_stl}")
    print(f"Output: {output_dir}")
    print("-" * 60)
    print(f"Volume difference: {comparison['volume_diff_percent']:.2f}%")
    print(f"Surface area difference: {comparison['surface_area_diff_percent']:.2f}%")
    print(f"Vertex count difference: {comparison['vertex_diff']}")
    print(f"Face count difference: {comparison['face_diff']}")
    print(f"Watertight match: {comparison['watertight_match']}")
    print("=" * 60)

    # Return non-zero if significant differences
    if (
        comparison["volume_diff_percent"] > 5
        or comparison["surface_area_diff_percent"] > 5
    ):
        logger.warning("Significant geometry differences detected!")
        sys.exit(1)

    logger.info("Visual diff complete!")


if __name__ == "__main__":
    main()
