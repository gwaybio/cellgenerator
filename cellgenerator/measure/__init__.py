"""CellProfiler feature extraction via an isolated conda environment.

The :class:`CellProfilerMeasurer` is the public entry point.  It invokes a
thin runner script inside the ``cg-cellprofiler`` conda environment so that
CellProfiler's dependency tree never conflicts with cellgenerator's own
dependencies.

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
>>> measurer = CellProfilerMeasurer()                     # doctest: +SKIP
>>> df = measurer.measure(img, dim=(200, 200), rotate=0)  # doctest: +SKIP
>>> df_sweep = measurer.measure_sweep(img, dim=(200, 200))# doctest: +SKIP

See :doc:`/setup/cellprofiler` for environment setup instructions.
"""

from ._measurer import CellProfilerMeasurer, CellProfilerNotFoundError

__all__ = ["CellProfilerMeasurer", "CellProfilerNotFoundError"]
