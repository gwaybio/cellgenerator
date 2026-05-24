# Rotation Sensitivity Analysis

Not all CellProfiler-compatible features are equal when a cell is rotated.
This section documents a systematic study of how `cp_measure` features respond
to rotation across a large grid of synthetic cells — and identifies which features
can be corrected, which are genuinely invariant, and which are artefacts of
our specific test set.

## Overview

We simulated **1,600 synthetic cells** across a factorial parameter grid and
rotated each cell through **72 angles** (0°–355° in 5° steps), measuring all
~372 `cp_measure` features at every angle.

| Parameter | Values |
|---|---|
| Mask shape | `EllipseMask` |
| Aspect ratio (x/y) | 1.0, 1.5, 2.0, 3.0, 4.0 |
| Cell size (y_radius px) | 60, 100, 150, 200 |
| Stain | `SpatialStain(σ=5/20/60)`, `ConstantStain` |
| Seeds per config | 20 |
| **Total measurements** | 1,600 × 72 = **115,200** |

The dataset is stored as an [OME-Arrow](https://github.com/wayscience/ome-arrow)
Parquet file with the intensity image and segmentation mask embedded alongside all
feature columns.

## Sensitivity metric: RSI

$$\text{RSI} = \frac{\text{mean within-cell variance across 72 angles}}
                    {\text{between-cell variance at angle = 0}}$$

- **RSI > 1**: rotation adds *more* variance than biology → orientation artefact
- **RSI < 0.01**: rotation contributes < 1% of biological spread → invariant in practice

## Key findings

| RSI threshold | Features | % of 359 non-constant features |
|---|---|---|
| RSI < 0.01 — **stable** | 130 | 36% |
| RSI < 0.10 | 223 | 62% |
| RSI < 1.00 | 291 | 81% |
| RSI ≥ 1.00 — **rotation dominates** | 68 | 19% |

### Category breakdown (median RSI)

| Category | Median RSI | Status |
|---|---|---|
| Moments (Central, Normalized, Spatial, InertiaTensor off-diag) | ≫ 1 | ❌ Sensitive — correctable post-hoc |
| RadialDistribution ZernikePhase | ~1.1 | ❌ Phase encodes orientation — correctable post-hoc |
| HuMoment 2–6 | ~15–800 | ⚠️ *Apparent* sensitivity — test-design artefact (see note) |
| Zernike_n_odd-m | ~0.5–4 | ⚠️ *Apparent* sensitivity — test-design artefact (see note) |
| Zernike_n_even-m / RadialDistribution ZernikeMag | ~0.01–0.16 | ≈ Small pixel-interpolation residual |
| Granularity | ~0.25 | ≈ Discrete structuring element; no analytical fix |
| Texture (Haralick) | ~0.011 | ✅ Invariant (4-direction GLCM average) |
| Intensity statistics | ~0.008 | ✅ Invariant |
| Shape (Area, Eccentricity, …) | ~0.003 | ✅ Invariant |
| Feret diameters | ~0.0002 | ✅ Invariant |

> **Test-design note:** `HuMoment_2–6` and `Zernike_n_odd-m` appear sensitive
> because our synthetic cells are symmetric ellipses.  Symmetric shapes have
> zero odd-order moments, so *every* cell has the same near-zero value — making
> between-cell variance tiny and the RSI ratio unreliable.  These features are
> **genuinely rotation-invariant** and should not be blocklisted.

## Notebooks

```{toctree}
:maxdepth: 1

analyze_rotation_sweep
feature_math
feature_corrections
```

- **`analyze_rotation_sweep`** — parameter coverage, inline cell images
  (via CytoDataFrame), RSI + CV distributions, full per-feature report.
  *Note: the CytoDataFrame interactive panels require a live Jupyter kernel;
  static outputs are rendered in the remaining cells.*

- **`feature_math`** — mathematical derivation of why each sensitive category
  is rotation-dependent, with the rotation transformation formulas and proposed
  correction strategies.

- **`feature_corrections`** — proof-of-concept post-hoc corrections applied to
  the full dataset.  Shows RSI before and after correction for moments,
  Zernike phases, and location features.

## Implications for pycytominer

Per-feature RSI scores and suggested corrections are embedded in
`schema/cellprofiler_mapping.json` in the
[gwaybio/cp_measure](https://github.com/gwaybio/cp_measure) repository.
This file is the intended input for generating a rotation-sensitivity blocklist
or correction pipeline in [pycytominer](https://github.com/cytomining/pycytominer).
