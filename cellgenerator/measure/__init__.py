"""CellProfiler-compatible feature extraction via `cp_measure`.

The :class:`CellProfilerMeasurer` is the public entry point.  It calls
`cp_measure` directly in-process — no conda environment or subprocess required.

Quick start
-----------
>>> from cellgenerator import Image
>>> from cellgenerator.mask import EllipseMask
>>> from cellgenerator.stain import SpatialStain
>>> from cellgenerator.measure import CellProfilerMeasurer
>>>
>>> img = Image(dim=(1000, 1000),
...             mask=EllipseMask(y_radius=200, x_radius=400),
...             stain=SpatialStain(y_corr=20, x_corr=20))
>>>
>>> measurer = CellProfilerMeasurer()
>>> df = measurer.measure(img, dim=(200, 200), rotate=0)   # doctest: +SKIP
>>> df_sweep = measurer.measure_sweep(img, dim=(200, 200)) # doctest: +SKIP
"""

from ._measurer import CellProfilerMeasurer

__all__ = ["CellProfilerMeasurer"]
