# CellProfiler-compatible features

cellgenerator extracts CellProfiler-compatible morphological features using
[**cp_measure**](https://github.com/afermg/cp_measure) — a pure-Python package
that implements the same measurement algorithms as CellProfiler without requiring
CellProfiler itself.

`cp_measure` is listed as a regular dependency in `pyproject.toml` and installs
automatically with cellgenerator:

```bash
pip install cellgenerator
```

No conda environment, no Java, no `mysql_config`, and no `CELLPROFILER_PYTHON`
variable are needed.

---

## Feature categories extracted

| Category | Examples |
|---|---|
| Size & shape | `Area`, `Perimeter`, `Eccentricity`, `Solidity`, … |
| Zernike moments | `Zernike_0_0`, `Zernike_2_0`, … |
| Feret diameters | `MinFeretDiameter`, `MaxFeretDiameter` |
| Intensity | `Intensity_MeanIntensity`, `Intensity_StdIntensity`, … |
| Texture (Haralick) | `AngularSecondMoment_3_00_256`, `Entropy_5_00_256`, … |
| Granularity | `Granularity_1`, `Granularity_2`, … |
| Radial distribution | `RadialDistribution_FracAtD_1of4`, … |
| Radial Zernikes | `RadialDistribution_ZernikeMagnitude_0_0`, … |

In total, `CellProfilerMeasurer` returns **~370 features** per measurement.

---

## Feature name differences from CellProfiler

cp_measure feature names differ slightly from CellProfiler column names:

| Category | cp_measure | CellProfiler |
|---|---|---|
| Shape | `Area` | `AreaShape_Area` |
| Intensity | `Intensity_MeanIntensity` | `Intensity_MeanIntensity_DNA` |
| Texture | `AngularSecondMoment_3_00_256` | `Texture_AngularSecondMoment_DNA_3_00_256` |
| Granularity | `Granularity_1` | `Granularity_1_DNA` |

A "good-enough" mapping between the two naming conventions is maintained in the
[cp_measure schema](https://github.com/gwaybio/cp_measure/blob/main/schema/cellprofiler_mapping.json).

---

## Quick start

```python
from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.stain import SpatialStain
from cellgenerator.measure import CellProfilerMeasurer

# Build a synthetic cell
img = Image(
    dim=(1000, 1000),
    mask=EllipseMask(y_radius=200, x_radius=400),
    stain=SpatialStain(y_corr=20, x_corr=20),
)

measurer = CellProfilerMeasurer()

# Single measurement → one-row DataFrame
df = measurer.measure(img, dim=(200, 200), rotate=0.0)
print(df.shape)           # (1, ~370)
print(df.columns[:10].tolist())

# 360° rotation sweep (36 angles × 10°)
df_sweep = measurer.measure_sweep(img, dim=(200, 200))
print(df_sweep.shape)     # (36, ~370)
```
