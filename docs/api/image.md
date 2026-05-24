# Image

The `Image` class is the main entry point. It composes a {doc}`mask <mask>`,
{doc}`stain <stain>`, and {doc}`noise <noise>` into a synthetic cell, then renders it
at any output resolution and rotation angle.

## Usage

```python
from cellgenerator import Image
from cellgenerator.mask import CircleMask, EllipseMask
from cellgenerator.stain import ConstantStain, SpatialStain

# Minimal — constant stain, no noise
img = Image(
    dim=(1000, 1000),
    mask=CircleMask(radius=300),
    stain=ConstantStain(),
)

# Sweep rotations (core use-case for CellProfiler sensitivity analysis)
for angle in range(0, 360, 10):
    img.save(f"cell_{angle:03d}.png", dim=(80, 80), rotate=angle)
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.Image
   :members:
   :special-members: __init__
   :show-inheritance:
```
