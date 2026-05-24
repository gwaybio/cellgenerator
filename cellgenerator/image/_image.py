"""Core Image class for synthetic cell generation."""

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage

from ..mask._abcmask import AbstractMask
from ..noise._abcnoise import AbstractNoise
from ..noise._const_noise import ConstantNoise
from ..stain._abcstain import AbstractStain


class Image:
    """Synthetic cell image composed of a mask, stain, and noise.

    The image is generated at a high internal resolution (``dim``) and can be
    rendered, plotted, or saved at any output resolution with optional rotation.
    This two-step approach lets you generate once and sample many angles cheaply.

    Parameters
    ----------
    dim : tuple[int, int]
        Internal resolution as ``(height, width)`` in pixels. Should be larger
        than the intended output resolution to allow downsampling.
    mask : AbstractMask
        Defines the spatial extent of the cell (which pixels are "inside").
    stain : AbstractStain
        Defines the intensity pattern across the cell.
    noise : AbstractNoise, optional
        Multiplicative pixel-level noise, by default
        :class:`~cellgenerator.noise.ConstantNoise` (no noise).
    stain_min : float, optional
        Minimum stain intensity after normalisation, by default ``0.4``.
        Must be in ``(0, 1]``.
    stain_max : float, optional
        Maximum stain intensity after normalisation, by default ``1.0``.
        Must be in ``(0, 1]`` and ``>= stain_min``.

    Raises
    ------
    TypeError
        If any argument has an unexpected type.
    ValueError
        If ``dim`` is invalid or stain range constraints are violated.

    Examples
    --------
    >>> from cellgenerator import Image
    >>> from cellgenerator.mask import EllipseMask
    >>> from cellgenerator.stain import SpatialStain
    >>> img = Image(
    ...     dim=(1000, 1000),
    ...     mask=EllipseMask(y_radius=200, x_radius=400),
    ...     stain=SpatialStain(y_corr=20, x_corr=20),
    ... )
    >>> pil_img = img.get_img(dim=(80, 80), rotate=35)
    >>> pil_img.size
    (80, 80)
    """

    def __init__(
        self,
        dim: tuple[int, int],
        mask: AbstractMask,
        stain: AbstractStain,
        noise: AbstractNoise = ConstantNoise(),
        stain_min: float = 0.4,
        stain_max: float = 1.0,
    ) -> None:
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")
        if not isinstance(mask, AbstractMask):
            raise TypeError("mask must be an AbstractMask instance")
        if not isinstance(stain, AbstractStain):
            raise TypeError("stain must be an AbstractStain instance")
        if not isinstance(noise, AbstractNoise):
            raise TypeError("noise must be an AbstractNoise instance")

        stain_min = float(stain_min)
        stain_max = float(stain_max)
        if not (0 < stain_min <= 1):
            raise ValueError("stain_min must be in (0, 1]")
        if not (0 < stain_max <= 1):
            raise ValueError("stain_max must be in (0, 1]")
        if stain_min > stain_max:
            raise ValueError("stain_min must be <= stain_max")

        self._dim = dim
        self._mask = mask._generate_mask(self._dim)
        self._stain = stain._generate_stain(self._dim)
        self._noise = noise
        self._stain_min = stain_min
        self._stain_max = stain_max

    def get_img(self, dim: tuple[int, int], rotate: float = 0.0) -> PILImage.Image:
        """Render the cell as a PIL grayscale image.

        The stain is normalised to ``[stain_min, stain_max]``, multiplied by
        the mask, noise is applied, and the result is scaled to uint8. The
        image is then rotated and resized to ``dim``.

        Parameters
        ----------
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.

        Returns
        -------
        PIL.Image.Image
            Grayscale (mode ``"L"``) PIL image of size ``dim``.

        Raises
        ------
        TypeError
            If ``dim`` entries are not integers or ``rotate`` is not numeric.
        ValueError
            If ``dim`` does not have exactly two elements.
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")

        rotate = float(rotate)

        # Work on a copy so repeated calls produce consistent results
        stain = self._stain.copy().astype(float)
        stain -= stain.min()
        stain_range = stain.max()
        if stain_range > 0:
            stain /= stain_range
        stain *= self._stain_max - self._stain_min
        stain += self._stain_min

        img = self._mask * stain
        img = self._noise._add_noise(img)
        img = (img * 255).astype(np.uint8)

        pil_img = PILImage.fromarray(img, mode="L")
        pil_img = pil_img.rotate(rotate)
        pil_img = pil_img.resize(dim)
        return pil_img

    def get_mask_img(self, dim: tuple[int, int], rotate: float = 0.0) -> PILImage.Image:
        """Render the cell mask as a uint8 label image.

        Returns the ground-truth segmentation mask at the requested output
        resolution and rotation, using nearest-neighbour resampling to preserve
        binary values.  Pixel values are ``0`` (background) or ``1`` (cell).

        This is the "trivial segmentation" step — because the cell is synthetic
        we already know exactly which pixels belong to it.  The returned image
        can be passed directly to CellProfiler as a pre-computed object mask.

        Parameters
        ----------
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.  Should match
            the ``dim`` passed to :meth:`get_img` so the mask aligns with the
            intensity image.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.  Must match the
            ``rotate`` used when generating the corresponding intensity image.

        Returns
        -------
        PIL.Image.Image
            Grayscale (mode ``"L"``) image of size ``dim``; pixel values are
            ``0`` (background) or ``1`` (cell object label).

        Raises
        ------
        TypeError
            If ``dim`` entries are not integers or ``rotate`` is not numeric.
        ValueError
            If ``dim`` does not have exactly two elements.

        Examples
        --------
        >>> from cellgenerator import Image
        >>> from cellgenerator.mask import CircleMask
        >>> from cellgenerator.stain import ConstantStain
        >>> img = Image(dim=(500, 500), mask=CircleMask(200), stain=ConstantStain())
        >>> mask_img = img.get_mask_img(dim=(80, 80), rotate=45)
        >>> import numpy as np
        >>> arr = np.array(mask_img)
        >>> set(arr.flat).issubset({0, 1})
        True
        """
        if not isinstance(dim, tuple) or len(dim) != 2:
            raise ValueError("dim must be a tuple of two integers")
        if not all(isinstance(d, int) for d in dim):
            raise TypeError("dim entries must be integers")

        rotate = float(rotate)

        # Convert boolean mask to uint8 label image: False→0, True→1
        label = self._mask.astype(np.uint8)
        pil_mask = PILImage.fromarray(label, mode="L")
        # Nearest-neighbour keeps values binary through rotate + resize
        pil_mask = pil_mask.rotate(rotate, resample=PILImage.Resampling.NEAREST)
        pil_mask = pil_mask.resize(dim, resample=PILImage.Resampling.NEAREST)
        return pil_mask

    def save_mask(self, path: str, dim: tuple[int, int], rotate: float = 0.0) -> None:
        """Save the cell mask label image to a PNG file.

        Parameters
        ----------
        path : str
            Destination file path (should end in ``.png``).
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.

        Raises
        ------
        ValueError
            If ``path`` is not a string.
        """
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        self.get_mask_img(dim, rotate).save(path, "PNG")

    def plot(self, dim: tuple[int, int], rotate: float = 0.0) -> None:
        """Display the cell image using matplotlib.

        Parameters
        ----------
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.
        """
        img = np.array(self.get_img(dim, rotate))
        plt.imshow(img, cmap="gray")
        plt.axis("off")
        plt.show()

    def save(self, path: str, dim: tuple[int, int], rotate: float = 0.0) -> None:
        """Save the cell image to a PNG file.

        Parameters
        ----------
        path : str
            Destination file path (should end in ``.png``).
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.

        Raises
        ------
        ValueError
            If ``path`` is not a string.
        """
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        self.get_img(dim, rotate).save(path, "PNG")
