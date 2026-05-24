# cellgenerator

**cellgenerator** generates synthetic cell images to study how
[CellProfiler](https://cellprofiler.org/) features respond to rotation.

CellProfiler features should be **rotation-invariant** — a cell is the same cell
regardless of its orientation in the image. In practice, some features are sensitive
to rotation, representing a measurement artefact rather than biology. This package
provides controlled synthetic images to:

1. **Identify** which CellProfiler features change with rotation
2. **Correct** rotation-sensitive features where possible
3. **Blocklist** uncorrectable features in [pycytominer](https://github.com/cytomining/pycytominer)

> Originally authored by [Hugh Warden](https://github.com/hwarden162).
> Forked and extended by [Gregory Way](https://github.com/gwaybio).

---

## Installation

::::{tab-set}

:::{tab-item} pip
```bash
pip install cellgenerator
```
:::

:::{tab-item} uv
```bash
uv add cellgenerator
```
:::

:::{tab-item} Development
```bash
git clone https://github.com/gwaybio/cellgenerator.git
cd cellgenerator
uv sync --all-extras
```
:::

::::

---

## Quick start

```python
from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.stain import SpatialStain

# Define cell shape and staining pattern
mask = EllipseMask(y_radius=200, x_radius=400)
stain = SpatialStain(y_corr=20, x_corr=20)

# Compose synthetic cell at high internal resolution
img = Image(dim=(1000, 1000), mask=mask, stain=stain)

# Render at output size with a 35° rotation
img.plot(dim=(80, 80), rotate=35)
img.save(path="cell.png", dim=(80, 80), rotate=35)
```

---

## Architecture

A `cellgenerator` image is composed of three independent components:

| Component | Role | Built-in classes |
|-----------|------|-----------------|
| {doc}`Mask <api/mask>` | Cell shape — boolean pixel array | `CircleMask`, `EllipseMask` |
| {doc}`Stain <api/stain>` | Intensity pattern inside the cell | `ConstantStain`, `SpatialStain` |
| {doc}`Noise <api/noise>` | Multiplicative pixel perturbation | `ConstantNoise` |
| {doc}`Image <api/image>` | Composes all three; renders at any rotation | — |

### Rendering pipeline

```
mask (bool)  ×  stain (normalised to [stain_min, stain_max])
        ↓
  apply noise  →  scale to uint8  →  rotate  →  resize  →  PIL Image
```

All three components are abstract base classes — subclass them to add new cell
shapes, staining models, or noise types.

---

## Contents

```{toctree}
:maxdepth: 1
:caption: Tutorials

tutorials/cellprofiler_features
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/image
api/mask
api/stain
api/noise
api/measure
```

```{toctree}
:maxdepth: 1
:caption: Setup

setup/cellprofiler
```

```{toctree}
:maxdepth: 1
:caption: Development

changelog
```
