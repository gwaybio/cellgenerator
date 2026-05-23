"""cellgenerator — synthetic cell image generation for CellProfiler analysis.

Generate synthetic cell images with controlled properties to study how
CellProfiler features respond to rotation and other transformations.

Basic usage
-----------
>>> from cellgenerator import Image
>>> from cellgenerator.mask import EllipseMask
>>> from cellgenerator.stain import SpatialStain
>>>
>>> img = Image(
...     dim=(1000, 1000),
...     mask=EllipseMask(y_radius=200, x_radius=400),
...     stain=SpatialStain(y_corr=20, x_corr=20),
... )
>>> img.save("cell.png", dim=(80, 80), rotate=35)
"""

from .image._image import Image

__all__ = ["Image"]
__version__ = "0.2.0"
