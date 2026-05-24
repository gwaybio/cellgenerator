# Measure

The `measure` module extracts CellProfiler-compatible features from synthetic cell images
using [cp_measure](https://github.com/gwaybio/cp_measure) — no CellProfiler installation,
conda environment, or subprocess required.

## Architecture

```
cellgenerator
─────────────────────────────────────────────────────────
CellProfilerMeasurer.measure(image, dim, rotate=0)
  │
  ├─ image.get_img(dim, rotate)       →  pixels  (H×W float64, [0, 1])
  ├─ image.get_mask_img(dim, rotate)  →  labels  (H×W int32,   0/1)
  │
  └─ _run_measurements(pixels, labels)
       │
       ├── measureobjectsizeshape.get_sizeshape(masks, pixels)
       ├── measureobjectsizeshape.get_zernike(masks, pixels)
       ├── measureobjectsizeshape.get_feret(masks, pixels)
       ├── measureobjectintensity.get_intensity(masks, pixels)
       ├── measuregranularity.get_granularity(mask, pixels)
       ├── measureobjectintensitydistribution.get_radial_distribution(labels, pixels)
       ├── measureobjectintensitydistribution.get_radial_zernikes(labels, pixels)
       └── measuretexture.get_texture(masks, pixels, scale=3/5/10)
            │
            └── pd.DataFrame  ← one row, ~372 columns
```

## Feature groups

| cp_measure module | Feature prefix(es) | CellProfiler equivalent | Count |
|---|---|---|---|
| `get_sizeshape` | *(no prefix)* — `Area`, `Eccentricity`, … | `AreaShape_*` | ~20 |
| `get_zernike` | `Zernike_n_m` | `AreaShape_Zernike_n_m` | 30 |
| `get_feret` | `MinFeretDiameter`, `MaxFeretDiameter` | `AreaShape_*` | 2 |
| `get_intensity` | `Intensity_*`, `Location_*` | `Intensity_*`, `Location_*` | ~19 |
| `get_granularity` | `Granularity_k` | `Granularity_k_*` | 16 |
| `get_radial_distribution` | `RadialDistribution_*` | `RadialDistribution_*` | ~20 |
| `get_radial_zernikes` | `RadialDistribution_Zernike{Mag,Phase}_n_m` | same with channel suffix | 60 |
| `get_texture` (×3 scales) | `AngularSecondMoment_*`, `Contrast_*`, … | `Texture_*` | ~200 |

**Total: ~372 features per cell.**

Feature naming follows `cp_measure` conventions, which differ from CellProfiler's
embedded channel/object naming.  A schema mapping and rotation sensitivity scores are
maintained in the
[gwaybio/cp_measure](https://github.com/gwaybio/cp_measure) fork under
`schema/cellprofiler_mapping.json`.

## Quick start

```python
from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.stain import SpatialStain
from cellgenerator.measure import CellProfilerMeasurer

img = Image(
    dim=(1000, 1000),
    mask=EllipseMask(y_radius=200, x_radius=400),
    stain=SpatialStain(y_corr=20, x_corr=20),
)

measurer = CellProfilerMeasurer()

# Single angle → one-row DataFrame with ~372 feature columns
df = measurer.measure(img, dim=(200, 200), rotate=0.0)

# Full rotation sweep (0°–350° in 10° steps by default)
df_sweep = measurer.measure_sweep(img, dim=(200, 200))
print(df_sweep.shape)  # (36, ~373)
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.measure.CellProfilerMeasurer
   :members:
   :special-members: __init__
   :show-inheritance:
```
