"""Constant (uniform) stain implementation."""

import numpy as np

from ._abcstain import AbstractStain


class ConstantStain(AbstractStain):
    """Stain with uniform intensity across the entire image.

    Produces a flat array filled with a single constant value. Useful as a
    baseline when stain variation is not desired.

    Parameters
    ----------
    const : float, optional
        Intensity value, by default ``1.0``. Must be in the range ``(0, 1]``.

    Raises
    ------
    TypeError
        If ``const`` is not numeric.
    ValueError
        If ``const`` is not in the range ``(0, 1]``.

    Examples
    --------
    >>> stain = ConstantStain(const=0.8)
    >>> arr = stain._generate_stain((100, 100))
    >>> float(arr[0, 0])
    0.8
    """

    def __init__(self, const: float = 1.0) -> None:
        const = float(const)
        if not (0 < const <= 1):
            raise ValueError("const must be in the range (0, 1]")
        self._const = const

    def _generate_stain(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate a uniform stain array.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Float array of shape ``dim`` filled with :attr:`_const`.
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")
        return np.ones(dim) * self._const
