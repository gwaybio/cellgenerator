# Tutorial: CellProfiler Features & Rotation Sensitivity

This tutorial walks through the full `cellgenerator` workflow end-to-end:

- Building synthetic cells with different shapes and staining patterns
- Extracting CellProfiler morphological features via an isolated conda environment
- Running a 360° rotation sweep to identify rotation-sensitive features
- Quantifying sensitivity with the coefficient of variation (CV)

It is aimed at scientists familiar with image-based profiling who may not be
familiar with CellProfiler's internals.

> **CellProfiler environment required for Sections 4–7.**
> Sections 1–3 (image generation and the rotation demo) run without any
> additional setup.  See {doc}`/setup/cellprofiler` for instructions on
> setting up the `cg-cellprofiler` conda environment.

```{toctree}
:maxdepth: 1

tutorial_cellprofiler_features
```
