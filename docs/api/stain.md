# Stain

A **stain** defines the intensity pattern across a synthetic cell. The output is a
float NumPy array that is normalised to `[stain_min, stain_max]` by `Image` before
rendering, so the absolute scale does not matter.

All stains extend `AbstractStain` and implement `_generate_stain(dim)`.

## Built-in stains

### ConstantStain

Uniform intensity everywhere inside the cell. Useful as a controlled baseline.

```python
from cellgenerator.stain import ConstantStain

stain = ConstantStain(const=0.8)  # or just ConstantStain() for full brightness
```

### SpatialStain

Spatially-correlated intensity variation produced by applying a Gaussian filter to
standard-normal random noise. This approximates the non-uniform staining seen in
real fluorescence microscopy.

```python
from cellgenerator.stain import SpatialStain

# Large sigma → broad, gradual gradients
stain = SpatialStain(y_corr=50, x_corr=50)

# Small sigma → fine-grained variation
stain = SpatialStain(y_corr=5, x_corr=5)
```

## Extending

Subclass `AbstractStain` to add new patterns:

```python
from cellgenerator.stain import AbstractStain
import numpy as np

class RadialStain(AbstractStain):
    """Intensity decreasing radially from the centre."""

    def _generate_stain(self, dim: tuple[int, int]) -> np.ndarray:
        y, x = np.ogrid[: dim[0], : dim[1]]
        cy, cx = dim[0] / 2.0, dim[1] / 2.0
        dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
        max_dist = np.sqrt(cy**2 + cx**2)
        return 1.0 - dist / max_dist
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.stain.AbstractStain
   :members:
   :show-inheritance:

.. autoclass:: cellgenerator.stain.ConstantStain
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: cellgenerator.stain.SpatialStain
   :members:
   :special-members: __init__
   :show-inheritance:
```
