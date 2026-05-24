# cellgenerator

[![Tests](https://github.com/gwaybio/cellgenerator/actions/workflows/tests.yml/badge.svg)](https://github.com/gwaybio/cellgenerator/actions/workflows/tests.yml)
[![Lint](https://github.com/gwaybio/cellgenerator/actions/workflows/lint.yml/badge.svg)](https://github.com/gwaybio/cellgenerator/actions/workflows/lint.yml)

**cellgenerator** is a Python package for creating synthetic cell images to study how
[CellProfiler](https://cellprofiler.org/)-compatible features respond to rotation.

CellProfiler features should ideally be **rotation-invariant** — a cell is the same
cell regardless of how it sits in the image frame.  In practice, some features are
sensitive to rotation, representing a measurement artefact rather than biology.
This package generates controlled synthetic images to:

1. **Identify** which CellProfiler features change with rotation
2. **Correct** rotation-sensitive features where possible
3. **Blocklist** features in [pycytominer](https://github.com/cytomining/pycytominer) where correction is not feasible

> Originally authored by [Hugh Warden](https://github.com/hwarden162).
> Forked and substantially extended by [Gregory Way](https://github.com/gwaybio).

---

## Installation

```bash
pip install cellgenerator
```

For development:

```bash
git clone https://github.com/gwaybio/cellgenerator.git
cd cellgenerator
uv sync --all-extras
```

**Optional — OME-Arrow support** (for the rotation sweep analysis notebooks):

```bash
uv pip install "ome-arrow>=0.0.9" --override /dev/stdin <<'EOF'
pillow>=10.0
centrosome>=1.3.3
EOF
```

---

## Quick start

```python
from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.stain import SpatialStain
from cellgenerator.measure import CellProfilerMeasurer

# Define cell shape and staining pattern
mask  = EllipseMask(y_radius=200, x_radius=400)
stain = SpatialStain(y_corr=20, x_corr=20)
img   = Image(dim=(1000, 1000), mask=mask, stain=stain)

img.plot(dim=(80, 80), rotate=35)

# Extract ~372 cp_measure features (no CellProfiler install needed)
measurer = CellProfilerMeasurer()
df = measurer.measure(img, dim=(200, 200))          # single angle
df_sweep = measurer.measure_sweep(img, dim=(200, 200))  # full 360° sweep
```

![example cell](example_images/spatial_stain_example.png)

---

## Rotation sensitivity findings

We simulated **1,600 synthetic cells** across a factorial parameter grid
(aspect ratio × cell size × stain type × random seed) and rotated each cell
through **72 angles** (0°–355° in 5° steps), measuring all ~372 `cp_measure`
features at every angle — **115,200 measurements total**.

Features are scored with the **Rotation Sensitivity Index (RSI)**:

$$\text{RSI} = \frac{\text{within-cell variance across rotation angles}}{\text{between-cell variance at 0°}}$$

An RSI of 1.0 means rotation adds as much variance as biological differences between cells.

### Feature stability summary

| RSI threshold | Features | % of total |
|---|---|---|
| RSI < 0.01 — **stable** | 130 | 36% |
| RSI 0.01 – 0.10 — low | 93 | 26% |
| RSI 0.10 – 1.0 — moderate | 62 | 17% |
| RSI > 1.0 — **rotation dominates** | 54 | 15% |
| Test-design artefact¹ | 20 | 6% |
| Constant (zero variance) | 13 | 4% |

> ¹ `HuMoment_2–6` and `Zernike_n_odd-m` appear sensitive because our symmetric
> ellipses have zero odd-order moments.  These features are **genuinely invariant**
> and should not be blocklisted — the high RSI is an artefact of testing on
> symmetric shapes.

### Category breakdown (median RSI)

| Feature category | Median RSI | Correctable? |
|---|---|---|
| Moments (Central, Normalized, Spatial, InertiaTensor) | ≫ 1 | ✅ Post-hoc (binomial rotation) |
| RadialDistribution ZernikePhase | ~1.1 | ✅ Post-hoc (phase − m × Orientation) |
| Granularity | ~0.25 | ⚠️ Requires pre-orientation at measurement |
| Texture (Haralick, 4-direction) | ~0.011 | — Already invariant |
| Intensity statistics | ~0.008 | — Already invariant |
| Shape (Area, Eccentricity, Feret) | < 0.003 | — Already invariant |

**Key correction results** (proof-of-concept on the simulation data):

| Feature | RSI before | RSI after correction | Improvement |
|---|---|---|---|
| `CentralMoment_1_1` | 1,036,114 | 54 | **19,000×** |
| `InertiaTensor_0_1` | 427,775 | 54 | **7,900×** |
| `NormalizedMoment_1_1` | 30,354 | 2.2 | **13,800×** |
| `ZernikePhase` features | up to 4.0 | 0.25–0.73 | **48–89%** |
| `Location_CenterMassDistance` (new) | 0.6–5.3 | 0.12 | **good** |

Full RSI scores for all 372 features are available in
[`schema/cellprofiler_mapping.json`](https://github.com/gwaybio/cp_measure/blob/main/schema/cellprofiler_mapping.json)
in the `gwaybio/cp_measure` repository and in
[`analysis/rotation_sensitivity_scores.csv`](analysis/rotation_sensitivity_scores.csv).

### Analysis notebooks

| Notebook | Description |
|---|---|
| [`analysis/analyze_rotation_sweep.ipynb`](analysis/analyze_rotation_sweep.ipynb) | Parameter coverage, inline cell images, RSI + CV distributions, full per-feature report |
| [`analysis/feature_math.ipynb`](analysis/feature_math.ipynb) | Mathematical derivations: why each sensitive category is rotation-dependent and what the correction formula is |
| [`analysis/feature_corrections.ipynb`](analysis/feature_corrections.ipynb) | Proof-of-concept corrections applied to the full dataset, before/after RSI comparison |

---

## Architecture

| Component | Role | Built-in classes |
|---|---|---|
| **Mask** | Cell shape (boolean pixel array) | `CircleMask`, `EllipseMask` |
| **Stain** | Intensity pattern inside the cell | `ConstantStain`, `SpatialStain` |
| **Noise** | Multiplicative pixel-level perturbation | `ConstantNoise` |
| **Image** | Composes all three; renders at any rotation | — |

All three components are abstract base classes — subclass them to add new cell
shapes, staining models, or noise types.

### Rendering pipeline

```
mask (bool array)  ×  stain (normalised to [stain_min, stain_max])
        ↓
  apply noise  →  scale to uint8  →  rotate  →  resize  →  PIL Image
```

---

## Development

```bash
pytest                                          # run tests
pytest --cov=cellgenerator                      # with coverage
ruff check . && ruff format --check .          # lint
ruff format .                                   # auto-format
```

---

## Roadmap

- [ ] Additional mask types (irregular/polygon cells)
- [ ] Additional stain types (radial gradient, multi-compartment)
- [ ] Additional noise types (Poisson, Gaussian)
- [x] cp_measure integration — no CellProfiler install needed
- [x] Rotation sensitivity analysis (RSI scoring across 372 features)
- [x] Per-feature correction proof-of-concept
- [ ] pycytominer blocklist and correction pipeline

---

## Citation

If you use this software, please cite the original author:

> Hugh Warden. *cellgenerator*. <https://github.com/hwarden162/cellgenerator>

## License

MIT — see [LICENSE](LICENSE).
