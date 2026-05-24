"""CellProfiler-compatible feature extraction via cp_measure."""

from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from ..image._image import Image

# Texture scales matching CellProfiler's MeasureTexture defaults
_TEXTURE_SCALES = (3, 5, 10)


def _run_measurements(pixels: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    """Call all cp_measure modules and collect results into a flat dict.

    Parameters
    ----------
    pixels : np.ndarray
        2-D float64 array in [0, 1] — the cell intensity image.
    labels : np.ndarray
        2-D int32 array — 0 = background, 1 = cell object.

    Returns
    -------
    dict[str, float]
        Feature name → scalar value for the single cell (object label 1).
    """
    from cp_measure.core import (  # type: ignore[import]
        measuregranularity,
        measureobjectintensity,
        measureobjectintensitydistribution,
        measureobjectsizeshape,
        measuretexture,
    )

    features: dict[str, float] = {}

    def _harvest(result: dict[str, np.ndarray]) -> None:
        """Extract index-0 scalar from each feature array and store."""
        for name, arr in result.items():
            try:
                val = float(arr[0])
                if np.isfinite(val):
                    features[name] = val
            except (IndexError, TypeError, ValueError):
                pass

    runners = [
        (
            "sizeshape",
            lambda: measureobjectsizeshape.get_sizeshape(masks=labels, pixels=pixels),
        ),
        (
            "zernike",
            lambda: measureobjectsizeshape.get_zernike(masks=labels, pixels=pixels),
        ),
        (
            "feret",
            lambda: measureobjectsizeshape.get_feret(masks=labels, pixels=pixels),
        ),
        (
            "intensity",
            lambda: measureobjectintensity.get_intensity(masks=labels, pixels=pixels),
        ),
        (
            "granularity",
            lambda: measuregranularity.get_granularity(mask=labels, pixels=pixels),
        ),
        (
            "radial_dist",
            lambda: measureobjectintensitydistribution.get_radial_distribution(
                labels=labels, pixels=pixels
            ),
        ),
        (
            "radial_zern",
            lambda: measureobjectintensitydistribution.get_radial_zernikes(
                labels=labels, pixels=pixels
            ),
        ),
    ]
    # Texture at three scales (matching CellProfiler defaults)
    for scale in _TEXTURE_SCALES:
        runners.append(
            (
                f"texture_scale{scale}",
                (
                    lambda s: (
                        lambda: measuretexture.get_texture(
                            masks=labels, pixels=pixels, scale=s
                        )
                    )
                )(scale),
            )
        )

    for name, fn in runners:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _harvest(fn())
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"[CellProfilerMeasurer] {name} failed: {exc}\n")

    return features


class CellProfilerMeasurer:
    """Extract CellProfiler-compatible features from a :class:`~cellgenerator.Image`.

    Uses `cp_measure <https://github.com/gwaybio/cp_measure>`_ to compute
    features in-process — no conda environment or subprocess required.

    Feature groups measured
    -----------------------
    - **AreaShape** (``get_sizeshape``, ``get_zernike``, ``get_feret``)
    - **Intensity** (``get_intensity``)
    - **Texture** (``get_texture``) at scales 3, 5, and 10
    - **Granularity** (``get_granularity``)
    - **RadialDistribution** (``get_radial_distribution``, ``get_radial_zernikes``)

    Feature naming note
    -------------------
    Column names follow `cp_measure` conventions, which differ from CellProfiler's
    embedded channel/object naming.  A schema mapping is available in the
    `gwaybio/cp_measure <https://github.com/gwaybio/cp_measure>`_ fork under
    ``schema/cellprofiler_mapping.json``.

    Examples
    --------
    >>> from cellgenerator import Image
    >>> from cellgenerator.mask import EllipseMask
    >>> from cellgenerator.stain import ConstantStain
    >>> from cellgenerator.measure import CellProfilerMeasurer
    >>> img = Image(dim=(500, 500), mask=EllipseMask(150, 80), stain=ConstantStain())
    >>> measurer = CellProfilerMeasurer()
    >>> df = measurer.measure(img, dim=(200, 200))  # doctest: +SKIP
    >>> df.shape[1] > 100                           # doctest: +SKIP
    True
    """

    def measure(
        self,
        image: Image,
        dim: tuple[int, int],
        rotate: float = 0.0,
    ) -> pd.DataFrame:
        """Extract all cp_measure features from *image* at *rotate* degrees.

        Parameters
        ----------
        image : Image
            The synthetic cell to measure.
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.

        Returns
        -------
        pandas.DataFrame
            Single-row DataFrame.  Columns are cp_measure feature names.
            An additional ``rotate_deg`` column records the rotation angle.
        """
        rotate = float(rotate)

        # Render intensity image and binary mask at the requested size
        pixels = np.array(image.get_img(dim, rotate)).astype(np.float64) / 255.0
        labels = np.array(image.get_mask_img(dim, rotate)).astype(np.int32)

        features = _run_measurements(pixels, labels)
        return pd.DataFrame([{"rotate_deg": rotate, **features}])

    def measure_sweep(
        self,
        image: Image,
        dim: tuple[int, int],
        angles: list[float] | None = None,
    ) -> pd.DataFrame:
        """Measure features across multiple rotation angles.

        Parameters
        ----------
        image : Image
            The synthetic cell to measure.
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels.
        angles : list[float], optional
            Rotation angles in degrees.  Defaults to
            ``[0, 10, 20, …, 350]`` (full 360° sweep in 10° steps).

        Returns
        -------
        pandas.DataFrame
            One row per angle, same columns as :meth:`measure`.
        """
        if angles is None:
            angles = [float(a) for a in range(0, 360, 10)]
        rows = [self.measure(image, dim, rotate=a) for a in angles]
        return pd.concat(rows, ignore_index=True)
