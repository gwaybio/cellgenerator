"""Abstract base class for cell stain generators."""

from abc import ABC, abstractmethod

import numpy as np


class AbstractStain(ABC):
    """Base class for all stain types.

    A stain defines the intensity pattern across a synthetic cell image.
    Subclasses implement :meth:`_generate_stain` to produce a float array
    of shape ``dim`` representing relative staining intensity at each pixel.
    Values are normalized downstream by :class:`~cellgenerator.Image` before
    rendering, so the absolute scale does not matter.
    """

    @abstractmethod
    def _generate_stain(self, dim: tuple[int, int]) -> np.ndarray:
        """Generate a stain intensity array of the given dimensions.

        Parameters
        ----------
        dim : tuple[int, int]
            Output array dimensions as ``(height, width)``.

        Returns
        -------
        np.ndarray
            Float array of shape ``dim`` representing stain intensity.
        """
