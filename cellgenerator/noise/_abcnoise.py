"""Abstract base class for image noise generators."""

from abc import ABC, abstractmethod

import numpy as np


class AbstractNoise(ABC):
    """Base class for all noise types.

    Noise is applied multiplicatively to the rendered cell image after masking
    and stain normalisation. Subclasses implement :meth:`_generate_noise` to
    produce a per-pixel multiplier array.

    The public entry point is :meth:`_add_noise`, which calls
    :meth:`_generate_noise` and clips the result to ``[0, 1]``.
    """

    @abstractmethod
    def _generate_noise(self, img: np.ndarray) -> np.ndarray:
        """Generate a noise multiplier array matching the image shape.

        Parameters
        ----------
        img : np.ndarray
            The current image array (2-D, float, values in ``[0, 1]``).
            Provided so that noise can be image-dependent (e.g. Poisson).

        Returns
        -------
        np.ndarray
            Float array of the same shape as ``img``; values are used as
            per-pixel multipliers.
        """

    def _add_noise(self, img: np.ndarray) -> np.ndarray:
        """Apply noise to an image array.

        Multiplies ``img`` by the output of :meth:`_generate_noise` and clips
        the result to ``[0, 1]``.

        Parameters
        ----------
        img : np.ndarray
            2-D float image array with values in ``[0, 1]``.

        Returns
        -------
        np.ndarray
            Noisy image clipped to ``[0, 1]``.

        Raises
        ------
        TypeError
            If ``img`` is not a :class:`numpy.ndarray`.
        ValueError
            If ``img`` is not 2-D.
        """
        if not isinstance(img, np.ndarray):
            raise TypeError("img must be a numpy array")
        if img.ndim != 2:
            raise ValueError("img must be a 2-D array")
        noise = self._generate_noise(img)
        return np.clip(img * noise, 0.0, 1.0)
