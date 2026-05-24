# Noise

**Noise** is applied multiplicatively to the rendered cell image after masking and
stain normalisation. It allows simulation of realistic pixel-level intensity
variation from imaging hardware.

All noise types extend `AbstractNoise` and implement `_generate_noise(img)`. The
base class provides `_add_noise(img)`, which calls `_generate_noise`, multiplies,
and clips to `[0, 1]`.

## Built-in noise types

### ConstantNoise

Returns a ones array — the multiplicative identity. This is the default in `Image`
and results in no noise being added.

```python
from cellgenerator.noise import ConstantNoise

noise = ConstantNoise()
```

## Extending

Subclass `AbstractNoise` to add new noise models:

```python
from cellgenerator.noise import AbstractNoise
import numpy as np

class GaussianNoise(AbstractNoise):
    """Additive Gaussian noise expressed as a multiplicative perturbation."""

    def __init__(self, sigma: float = 0.05) -> None:
        self._sigma = sigma

    def _generate_noise(self, img: np.ndarray) -> np.ndarray:
        return np.random.normal(loc=1.0, scale=self._sigma, size=img.shape)


class PoissonNoise(AbstractNoise):
    """Poisson (shot) noise — scales with local intensity."""

    def __init__(self, scale: float = 50.0) -> None:
        self._scale = scale

    def _generate_noise(self, img: np.ndarray) -> np.ndarray:
        counts = np.random.poisson(img * self._scale)
        return counts / (img * self._scale + 1e-8)
```

## Class reference

```{eval-rst}
.. autoclass:: cellgenerator.noise.AbstractNoise
   :members:
   :show-inheritance:

.. autoclass:: cellgenerator.noise.ConstantNoise
   :members:
   :show-inheritance:
```
