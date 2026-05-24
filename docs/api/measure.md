# Measure

The `measure` module extracts CellProfiler features from synthetic cell images by
invoking a runner script inside a dedicated conda environment.  See
{doc}`/setup/cellprofiler` for one-time setup instructions.

## Architecture

```
cellgenerator (main env)         cg-cellprofiler conda env
─────────────────────────        ─────────────────────────
CellProfilerMeasurer
  │
  ├─ image.get_img()        →    temp/cell.png
  ├─ image.get_mask_img()   →    temp/mask.png
  │
  └─ subprocess ──────────────▶  _runner.py
                                   │ set_headless()
                                   │ build workspace
                                   │ MeasureObjectSizeShape
                                   │ MeasureObjectIntensity
                                   │ MeasureTexture
                                   │ MeasureGranularity
                                   └─ MeasureObjectRadialDistribution
                                        │
  pd.DataFrame  ◀── JSON ─────────────┘
```

## Feature modules

| CellProfiler module | Feature prefix | Description |
|---|---|---|
| `MeasureObjectSizeShape` | `AreaShape_*` | Area, perimeter, eccentricity, orientation, Zernike moments |
| `MeasureObjectIntensity` | `Intensity_*` | Mean, max, min, std, integrated intensity |
| `MeasureTexture` | `Texture_*` | Haralick texture features at multiple scales |
| `MeasureGranularity` | `Granularity_*` | Granularity spectrum |
| `MeasureObjectRadialDistribution` | `RadialDistribution_*` | Zernike moments of radial intensity |

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

# Single angle
df = measurer.measure(img, dim=(200, 200), rotate=0.0)

# Full rotation sweep — the core use-case
df_sweep = measurer.measure_sweep(img, dim=(200, 200))
# df_sweep has 36 rows (0°–350° in 10° steps), ~200+ feature columns
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.measure.CellProfilerMeasurer
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoexception:: cellgenerator.measure.CellProfilerNotFoundError
   :show-inheritance:
```
