"""Spatially-correlated stain implementation."""

import numpy as np
from scipy.ndimage import gaussian_filter

from ._abcstain import AbstractStain


class SpatialStain(AbstractStain):
    """Stain with spatially-correlated intensity variation.

    Generates a realistic staining pattern by applying a Gaussian filter to
    standard-normal random noise. The correlation lengths control how smoothly
    the stain varies across the cell — larger values produce broad, gradual
    gradients while smaller values produce fine-grained variation.

    Parameters
    ----------
    y_corr : float
        Gaussian smoothing sigma along the vertical (y) axis, in pixels.
    x_corr : float
        Gaussian smoothing sigma along the horizontal (x) axis, in pixels.

    Raises
    ------
    TypeError
        If either correlation length is not numeric.
    ValueError
        If either correlation length is not positive.

    Examples
    --------
    >>> stain = SpatialStain(y_corr=20, x_corr=20)
    >>> arr = stain._generate_stain((500, 500))
    >>> arr.shape
    (500, 500)
    """

    def __init__(self, y_corr: float, x_corr: float) -> None:
        y_corr = float(y_corr)
        x_corr = float(x_corr)
        if y_corr <= 0:
            raise ValueError("y_corr must be positive")
        if x_corr <= 0:
            raise ValueError("x_corr must be positive")
        self._y_corr = y_corr
        self._x_corr = x_corr

    def _generate_stain(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate a spatially-correlated stain array.

        Draws standard-normal random noise and smooths it with a Gaussian
        filter to introduce spatial correlation.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Float array of shape ``dim`` with correlated intensity values.
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")

        noise = np.random.normal(loc=0.0, scale=1.0, size=dim)
        return gaussian_filter(noise, sigma=(self._y_corr, self._x_corr))
