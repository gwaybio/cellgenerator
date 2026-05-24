# CellProfiler environment setup

cellgenerator extracts CellProfiler features by invoking a thin runner script
inside a **dedicated conda environment** (`cg-cellprofiler`).  This keeps
CellProfiler's dependency tree (which pins `docutils==0.15.2`) from conflicting
with cellgenerator's own docs and dev dependencies.

You only need to do this setup once.

---

## Prerequisites

- [conda](https://docs.conda.io/en/latest/miniconda.html) or
  [mamba](https://mamba.readthedocs.io/) installed
- The `cellgenerator` repository cloned locally

---

## 1. Create the environment

From the repository root:

```bash
conda env create -f environment.yml
```

This installs CellProfiler ≥ 4.2 via conda-forge, which ships prebuilt binary
wheels — no C compiler required.

To update an existing environment after pulling changes:

```bash
conda env update -f environment.yml --prune
```

---

## 2. Tell cellgenerator where to find it

cellgenerator needs to know which Python interpreter has CellProfiler installed.
There are three ways to provide this, in priority order:

### Option A — environment variable (recommended)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export CELLPROFILER_PYTHON="$HOME/miniconda3/envs/cg-cellprofiler/bin/python"
```

Adjust the path prefix (`miniconda3`, `anaconda3`, `/opt/conda`, etc.) to match
your conda installation.  You can find the exact path with:

```bash
conda run -n cg-cellprofiler which python
```

### Option B — pass the path explicitly

```python
from cellgenerator.measure import CellProfilerMeasurer

measurer = CellProfilerMeasurer(
    python="/home/user/miniconda3/envs/cg-cellprofiler/bin/python"
)
```

### Option C — auto-discovery (zero config)

`CellProfilerMeasurer()` automatically searches for the `cg-cellprofiler` env
in common conda locations:

- `~/miniconda3/envs/cg-cellprofiler/bin/python`
- `~/anaconda3/envs/cg-cellprofiler/bin/python`
- `~/.conda/envs/cg-cellprofiler/bin/python`
- `/opt/conda/envs/cg-cellprofiler/bin/python`

If your conda is installed elsewhere, use Option A or B.

---

## 3. Verify the setup

```python
from cellgenerator.measure import CellProfilerMeasurer

measurer = CellProfilerMeasurer()
print(measurer.python)   # prints the interpreter path
```

Or from the command line:

```bash
$CELLPROFILER_PYTHON cellgenerator/measure/_runner.py --check
# → {"status": "ok", "cellprofiler": "4.2.8.1", "cellprofiler_core": "4.2.8.1"}
```

---

## 4. Extract features

```python
from cellgenerator import Image
from cellgenerator.mask import EllipseMask
from cellgenerator.stain import SpatialStain
from cellgenerator.measure import CellProfilerMeasurer

# Build the synthetic cell
img = Image(
    dim=(1000, 1000),
    mask=EllipseMask(y_radius=200, x_radius=400),
    stain=SpatialStain(y_corr=20, x_corr=20),
)

measurer = CellProfilerMeasurer()

# Single measurement
df = measurer.measure(img, dim=(200, 200), rotate=0.0)
print(df.shape)          # (1, ~200+)
print(df.columns[:10])

# Full 360° sweep (36 angles × 10°)
df_sweep = measurer.measure_sweep(img, dim=(200, 200))
print(df_sweep.shape)    # (36, ~200+)
```

---

## Troubleshooting

**`CellProfilerNotFoundError`**
: The `cg-cellprofiler` env was not found in any standard location and
  `CELLPROFILER_PYTHON` is not set.  Run `conda run -n cg-cellprofiler which python`
  and set `CELLPROFILER_PYTHON` to the output.

**`conda: command not found`**
: Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) first.

**Module measurement errors** (warnings, not failures)
: Some CellProfiler modules may print warnings to stderr — these are captured
  and forwarded but do not abort the measurement.  Features from the failing
  module are simply absent from the output DataFrame.
