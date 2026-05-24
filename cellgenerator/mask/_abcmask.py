"""Abstract base class for cell mask generators."""

from abc import ABC, abstractmethod

import numpy as np


class AbstractMask(ABC):
    """Base class for all mask types.

    A mask defines the spatial extent of a synthetic cell within an image.
    Subclasses implement :meth:`_generate_mask` to produce a boolean array
    of shape ``dim`` where ``True`` pixels are inside the cell.
    """

    @abstractmethod
    def _generate_mask(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate a boolean mask of the given dimensions.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Boolean array of shape ``dim``; ``True`` inside the cell boundary.
        """
