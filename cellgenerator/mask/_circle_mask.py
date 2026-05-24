"""Circular mask implementation."""

import numpy as np

from ._abcmask import AbstractMask


class CircleMask(AbstractMask):
    """Mask shaped as a circle centered in the image.

    A special case of :class:`EllipseMask` where both radii are equal.

    Parameters
    ----------
    radius : float
        Radius of the circle in pixels.

    Raises
    ------
    TypeError
        If ``radius`` is not numeric.
    ValueError
        If ``radius`` is not positive.

    Examples
    --------
    >>> mask = CircleMask(radius=150)
    >>> arr = mask._generate_mask((500, 500))
    >>> arr.shape
    (500, 500)
    >>> arr.dtype
    dtype('bool')
    """

    def __init__(self, radius: float) -> None:
        radius = float(radius)
        if radius <= 0:
            raise ValueError("radius must be positive")
        self._radius = radius

    def _generate_mask(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate a circular boolean mask.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Boolean array of shape ``dim``; ``True`` inside the circle.
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")

        y, x = np.ogrid[: dim[0], : dim[1]]
        center_y, center_x = dim[0] / 2.0, dim[1] / 2.0
        dist = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        return dist <= self._radius
