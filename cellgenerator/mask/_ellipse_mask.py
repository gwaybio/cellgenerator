"""Elliptical mask implementation."""

import numpy as np

from ._abcmask import AbstractMask


class EllipseMask(AbstractMask):
    """Mask shaped as an axis-aligned ellipse centered in the image.

    Parameters
    ----------
    y_radius : float
        Radius of the ellipse along the vertical (y) axis, in pixels.
    x_radius : float
        Radius of the ellipse along the horizontal (x) axis, in pixels.

    Raises
    ------
    TypeError
        If either radius is not numeric.
    ValueError
        If either radius is not positive.

    Examples
    --------
    >>> mask = EllipseMask(y_radius=200, x_radius=400)
    >>> arr = mask._generate_mask((500, 500))
    >>> arr.shape
    (500, 500)
    >>> arr.dtype
    dtype('bool')
    """

    def __init__(self, y_radius: float, x_radius: float) -> None:
        y_radius = float(y_radius)
        x_radius = float(x_radius)
        if y_radius <= 0:
            raise ValueError("y_radius must be positive")
        if x_radius <= 0:
            raise ValueError("x_radius must be positive")
        self._y_radius = y_radius
        self._x_radius = x_radius

    def _generate_mask(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate an elliptical boolean mask.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Boolean array of shape ``dim``; ``True`` inside the ellipse.
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")

        y, x = np.ogrid[: dim[0], : dim[1]]
        center_y, center_x = dim[0] / 2.0, dim[1] / 2.0
        normalized_dist = np.sqrt(
            ((x - center_x) / self._x_radius) ** 2
            + ((y - center_y) / self._y_radius) ** 2
        )
        return normalized_dist <= 1.0
