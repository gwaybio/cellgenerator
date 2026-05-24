"""Simulate 1,600 synthetic cells × 72 rotation angles with cp_measure features.

Parameter grid (80 configs × 20 seeds = 1,600 cells × 72 angles = 115,200 rows):

  Mask: EllipseMask
    aspect_ratio (x_radius / y_radius): 1.0, 1.5, 2.0, 3.0, 4.0
    y_radius (px, internal 1000×1000 canvas): 60, 100, 150, 200

  Stain:
    SpatialStain(corr=5)   — fine-grained spatially-correlated noise
    SpatialStain(corr=20)  — medium-scale noise
    SpatialStain(corr=60)  — coarse gradients
    ConstantStain          — uniform intensity (no spatial variation)

  Seeds: 0..19 per config (controls numpy random state for stain generation)
  Angles: 0°, 5°, 10°, …, 355° (72 steps)

Output
------
  analysis/rotation_dataset.ome.parquet

  Columns:
    cell_id       int32    — unique cell identifier (1-based)
    angle_deg     float32  — rotation angle in degrees
    aspect_ratio  float32  — x_radius / y_radius
    y_radius      int16    — y_radius of EllipseMask in pixels
    stain_type    string   — "spatial" or "constant"
    stain_corr    float32  — Gaussian sigma for SpatialStain (0 for ConstantStain)
    seed          int16    — numpy random seed used
    image         struct   — OME-Arrow struct (128×128 uint8 grayscale)
    mask          struct   — OME-Arrow struct (128×128 uint8 label, 0/1)
    <feature>     float32  — one column per cp_measure feature (~373 total)

Usage
-----
  uv run python analysis/simulate_rotation_sweep.py
  uv run python analysis/simulate_rotation_sweep.py --dry-run   # 10 rows, timing only
  uv run python analysis/simulate_rotation_sweep.py --out /path/to/out.ome.parquet
"""

from __future__ import annotations

import argparse
import itertools
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from ome_arrow import OME_ARROW_STRUCT, from_numpy

from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.measure._measurer import _run_measurements
from cellgenerator.stain import ConstantStain, SpatialStain

# ---------------------------------------------------------------------------
# Parameter grid
# ---------------------------------------------------------------------------

ASPECT_RATIOS: list[float] = [1.0, 1.5, 2.0, 3.0, 4.0]
Y_RADII: list[int] = [60, 100, 150, 200]
STAIN_CONFIGS: list[tuple[str, int]] = [
    ("spatial",   5),
    ("spatial",  20),
    ("spatial",  60),
    ("constant",  0),
]
N_SEEDS: int = 20
ANGLES: list[int] = list(range(0, 360, 5))   # 72 angles
RENDER_DIM: tuple[int, int] = (128, 128)
INTERNAL_DIM: tuple[int, int] = (1000, 1000)
BATCH_SIZE: int = 500
DEFAULT_OUT = Path(__file__).parent / "rotation_dataset.ome.parquet"

# ---------------------------------------------------------------------------
# Cell construction
# ---------------------------------------------------------------------------

def make_image(
    aspect_ratio: float,
    y_radius: int,
    stain_type: str,
    stain_corr: int,
    seed: int,
) -> Image:
    """Return a reproducible synthetic cell.

    ``np.random.seed`` is set immediately before Image construction so that
    all numpy randomness inside SpatialStain._generate_stain is deterministic.
    """
    np.random.seed(seed)
    x_radius = max(1, int(y_radius * aspect_ratio))
    mask = EllipseMask(y_radius=y_radius, x_radius=x_radius)
    stain: ConstantStain | SpatialStain
    if stain_type == "spatial":
        stain = SpatialStain(y_corr=float(stain_corr), x_corr=float(stain_corr))
    else:
        stain = ConstantStain()
    return Image(dim=INTERNAL_DIM, mask=mask, stain=stain)


def render(img: Image, angle: float) -> tuple[np.ndarray, np.ndarray]:
    """Render image and mask at *angle* degrees.

    Returns
    -------
    pixels : float64 array in [0, 1], shape RENDER_DIM (H, W)
    labels : int32 binary label array (0=bg, 1=cell), shape RENDER_DIM
    """
    pixels = np.array(img.get_img(RENDER_DIM, angle)).astype(np.float64) / 255.0
    labels = np.array(img.get_mask_img(RENDER_DIM, angle)).astype(np.int32)
    return pixels, labels


# ---------------------------------------------------------------------------
# OME-Arrow helpers
# ---------------------------------------------------------------------------

def to_ome_dict(array_2d: np.ndarray) -> dict:
    """Convert a 2D numpy array to an OME-Arrow struct dict.

    The dict is used rather than keeping pa.StructScalar objects in memory,
    so that Arrow arrays can be reconstructed cleanly per batch.
    """
    return from_numpy(array_2d, dim_order="YX").as_py()


# ---------------------------------------------------------------------------
# Batch → PyArrow Table
# ---------------------------------------------------------------------------

_META_KEYS = frozenset(
    ["cell_id", "angle_deg", "aspect_ratio", "y_radius",
     "stain_type", "stain_corr", "seed", "image", "mask"]
)


def build_table(rows: list[dict]) -> pa.Table:
    """Convert a list of row dicts into a typed PyArrow Table."""
    image_col = pa.array([r["image"] for r in rows], type=OME_ARROW_STRUCT)
    mask_col  = pa.array([r["mask"]  for r in rows], type=OME_ARROW_STRUCT)

    arrays: dict[str, pa.Array] = {
        "cell_id":      pa.array([r["cell_id"]      for r in rows], type=pa.int32()),
        "angle_deg":    pa.array([r["angle_deg"]     for r in rows], type=pa.float32()),
        "aspect_ratio": pa.array([r["aspect_ratio"]  for r in rows], type=pa.float32()),
        "y_radius":     pa.array([r["y_radius"]      for r in rows], type=pa.int16()),
        "stain_type":   pa.array([r["stain_type"]    for r in rows]),
        "stain_corr":   pa.array([r["stain_corr"]    for r in rows], type=pa.float32()),
        "seed":         pa.array([r["seed"]          for r in rows], type=pa.int16()),
        "image":        image_col,
        "mask":         mask_col,
    }

    # Feature columns — float32 to save space
    feature_keys = [k for k in rows[0] if k not in _META_KEYS]
    for k in feature_keys:
        arrays[k] = pa.array(
            [r.get(k, float("nan")) for r in rows], type=pa.float32()
        )

    return pa.table(arrays)


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------

def run(
    out_path: Path,
    dry_run: bool = False,
) -> None:
    configs = list(itertools.product(ASPECT_RATIOS, Y_RADII, STAIN_CONFIGS))
    n_cells = len(configs) * N_SEEDS          # 1,600
    n_rows  = n_cells * len(ANGLES)           # 115,200
    max_rows = 10 if dry_run else n_rows

    print(f"Configs:  {len(configs):>6,}")
    print(f"Cells:    {n_cells:>6,}")
    print(f"Angles:   {len(ANGLES):>6,}")
    print(f"Rows:     {n_rows:>6,}  {'(dry-run: 10)' if dry_run else ''}")
    print(f"Output:   {out_path}")
    print()

    writer: pq.ParquetWriter | None = None
    batch: list[dict] = []
    rows_written = 0
    cell_id = 0
    t0 = time.perf_counter()

    outer_loop = itertools.product(configs, range(N_SEEDS))
    for (aspect_ratio, y_radius, (stain_type, stain_corr)), seed in outer_loop:
        if rows_written >= max_rows:
            break

        cell_id += 1
        img = make_image(aspect_ratio, y_radius, stain_type, stain_corr, seed)

        for angle in ANGLES:
            if rows_written + len(batch) >= max_rows:
                break

            pixels, labels = render(img, float(angle))
            features = _run_measurements(pixels, labels)

            batch.append({
                "cell_id":      cell_id,
                "angle_deg":    float(angle),
                "aspect_ratio": float(aspect_ratio),
                "y_radius":     int(y_radius),
                "stain_type":   stain_type,
                "stain_corr":   float(stain_corr),
                "seed":         int(seed),
                "image":        to_ome_dict((pixels * 255).astype(np.uint8)),
                "mask":         to_ome_dict(labels.astype(np.uint8)),
                **features,
            })

        # Flush batch when full or at the end of a cell's angles
        if len(batch) >= BATCH_SIZE or (dry_run and len(batch) > 0):
            table = build_table(batch)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema, compression="zstd")
            writer.write_table(table)
            rows_written += len(batch)
            elapsed = time.perf_counter() - t0
            rate = rows_written / elapsed
            eta_s = (max_rows - rows_written) / rate if rate > 0 else float("inf")
            print(
                f"  {rows_written:>7,} / {max_rows:,}"
                f"  ({100 * rows_written / max_rows:.1f}%)"
                f"  {rate:.1f} rows/s"
                f"  ETA {eta_s / 60:.1f} min"
                f"  cell {cell_id}/{n_cells}",
                flush=True,
            )
            batch = []

    # Flush tail
    if batch:
        table = build_table(batch)
        if writer is None:
            writer = pq.ParquetWriter(out_path, table.schema, compression="zstd")
        writer.write_table(table)
        rows_written += len(batch)

    if writer:
        writer.close()

    elapsed = time.perf_counter() - t0
    size_mb = out_path.stat().st_size / 1e6
    print()
    print(f"Done.  {rows_written:,} rows in {elapsed:.1f}s  →  {out_path}")
    print(f"File size: {size_mb:.1f} MB")

    if dry_run:
        rate = rows_written / elapsed
        est_h = (n_rows / rate) / 3600
        print(f"\nFull-run estimate at {rate:.1f} rows/s: {est_h:.1f} h  ({n_rows:,} rows)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output .ome.parquet path (default: analysis/rotation_dataset.ome.parquet)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process only 10 rows and print a full-run time estimate, then exit.",
    )
    args = parser.parse_args()
    run(out_path=args.out, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
