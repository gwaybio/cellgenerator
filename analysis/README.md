# Analysis: Rotation Sweep

This directory contains the simulation and analysis for the CellProfiler feature
rotation sensitivity study.

## Overview

We simulate **1,600 synthetic cells** across a factorial parameter grid and rotate
each cell through **72 angles** (0°–355° in 5° steps), measuring all cp_measure
features at every angle.  The result is a tidy Parquet file with one row per
(cell, angle) pair and ~372 feature columns, with the source image and mask
embedded as OME-Arrow structs.

## Parameter grid (80 configs × 20 seeds = 1,600 cells)

| Parameter | Values |
|---|---|
| Mask | `EllipseMask` |
| Aspect ratio (x/y) | 1.0, 1.5, 2.0, 3.0, 4.0 |
| y_radius (px) | 60, 100, 150, 200 |
| Stain | `SpatialStain(σ=5)`, `SpatialStain(σ=20)`, `SpatialStain(σ=60)`, `ConstantStain` |
| Seeds per config | 20 (controls `np.random.seed` for stain noise) |
| Angles | 0°, 5°, …, 355° (72 steps) |

**Total rows:** 1,600 × 72 = **115,200 measurements**

## Files

| File | Description |
|---|---|
| `simulate_rotation_sweep.py` | Simulation script — generates `rotation_dataset.ome.parquet` |
| `analyze_rotation_sweep.ipynb` | Analysis notebook (run after simulation) |
| `rotation_dataset.ome.parquet` | Output dataset (**gitignored**, ~large) |

## Running the simulation

```bash
# Quick smoke test (10 rows + time estimate):
uv run python analysis/simulate_rotation_sweep.py --dry-run

# Full run (~4 hours):
uv run python analysis/simulate_rotation_sweep.py
```

### Prerequisites

`ome-arrow` must be installed separately (it conflicts with `centrosome`'s
`pillow<12` pin in the lock file):

```bash
uv pip install "ome-arrow>=0.0.9" --override /dev/stdin <<'EOF'
pillow>=10.0
centrosome>=1.3.3
EOF
```

## Output schema

| Column | Type | Description |
|---|---|---|
| `cell_id` | int32 | Unique cell identifier (1-based) |
| `angle_deg` | float32 | Rotation angle in degrees |
| `aspect_ratio` | float32 | x_radius / y_radius |
| `y_radius` | int16 | EllipseMask y_radius in pixels |
| `stain_type` | string | `"spatial"` or `"constant"` |
| `stain_corr` | float32 | Gaussian σ for SpatialStain; 0 for ConstantStain |
| `seed` | int16 | numpy random seed |
| `image` | OME-Arrow struct | 128×128 uint8 grayscale intensity image |
| `mask` | OME-Arrow struct | 128×128 uint8 binary cell mask (0/1) |
| `Area`, `Eccentricity`, … | float32 | ~372 cp_measure feature columns |
