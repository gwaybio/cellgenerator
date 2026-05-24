# Mask

A **mask** defines the spatial extent of a synthetic cell — which pixels are "inside"
the cell boundary. The output is a boolean NumPy array of the requested dimensions.

All masks extend `AbstractMask` and implement `_generate_mask(dim)`.

## Built-in masks

### CircleMask

A circular mask centered in the image. Useful as a baseline because a circle is
already rotation-invariant — rotating it should produce no change in CellProfiler
features.

```python
from cellgenerator.mask import CircleMask

mask = CircleMask(radius=300)
arr = mask._generate_mask((1000, 1000))  # bool array, shape (1000, 1000)
```

### EllipseMask

An axis-aligned elliptical mask. Because an ellipse *is* sensitive to rotation,
this is the primary shape for probing rotation sensitivity in CellProfiler features.

```python
from cellgenerator.mask import EllipseMask

mask = EllipseMask(y_radius=200, x_radius=400)
arr = mask._generate_mask((1000, 1000))
```

## Extending

Subclass `AbstractMask` to add new shapes:

```python
from cellgenerator.mask import AbstractMask
import numpy as np

class RectangleMask(AbstractMask):
    def __init__(self, height: int, width: int) -> None:
        self._h = height
        self._w = width

    def _generate_mask(self, dim: tuple[int, int]) -> np.ndarray:
        mask = np.zeros(dim, dtype=bool)
        cy, cx = dim[0] // 2, dim[1] // 2
        mask[cy - self._h // 2 : cy + self._h // 2,
             cx - self._w // 2 : cx + self._w // 2] = True
        return mask
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.mask.AbstractMask
   :members:
   :show-inheritance:

.. autoclass:: cellgenerator.mask.CircleMask
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: cellgenerator.mask.EllipseMask
   :members:
   :special-members: __init__
   :show-inheritance:
```
