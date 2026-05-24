"""Constant (no-op) noise implementation."""

import numpy as np

from ._abcnoise import AbstractNoise


class ConstantNoise(AbstractNoise):
    """Noise that leaves the image unchanged.

    Returns a ones array so the multiplicative noise step is a no-op.
    Useful as the default when no stochastic pixel variation is desired.

    Examples
    --------
    >>> import numpy as np
    >>> noise = ConstantNoise()
    >>> img = np.full((10, 10), 0.5)
    >>> result = noise._add_noise(img)
    >>> float(result[0, 0])
    0.5
    """

    def _generate_noise(self, img: np.ndarray) -> np.ndarray:
        """Return a ones array — multiplicative identity.

        Parameters
        ----------
        img : np.ndarray
            2-D image array (used only to determine output shape).

        Returns
        -------
        np.ndarray
            Array of ones with the same shape as ``img``.
        """
        return np.ones_like(img)
