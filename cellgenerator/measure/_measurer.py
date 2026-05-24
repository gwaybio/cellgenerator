"""CellProfiler feature extraction via an isolated conda environment."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ..image._image import Image

# Path to the runner script that ships alongside this module
_RUNNER = Path(__file__).parent / "_runner.py"

# Ordered list of candidate Python executables to try when the user has not
# provided one explicitly.
_CANDIDATE_PYTHONS: list[Path] = [
    # Common miniconda / anaconda env locations
    Path.home() / "miniconda3" / "envs" / "cg-cellprofiler" / "bin" / "python",
    Path.home() / "anaconda3" / "envs" / "cg-cellprofiler" / "bin" / "python",
    Path.home() / "opt" / "anaconda3" / "envs" / "cg-cellprofiler" / "bin" / "python",
    Path.home() / ".conda" / "envs" / "cg-cellprofiler" / "bin" / "python",
    # conda default prefix / envs directory
    Path("/opt/conda/envs/cg-cellprofiler/bin/python"),
]


class CellProfilerNotFoundError(RuntimeError):
    """Raised when no usable CellProfiler Python interpreter can be located."""


class CellProfilerMeasurer:
    """Extract CellProfiler features from a :class:`~cellgenerator.Image`.

    The measurer runs :mod:`cellgenerator.measure._runner` as a subprocess
    inside a dedicated CellProfiler conda environment, so CellProfiler's heavy
    dependency tree never conflicts with cellgenerator's own dependencies.

    Parameters
    ----------
    python : str or Path, optional
        Explicit path to the Python interpreter that has CellProfiler
        installed.  If omitted the measurer searches for the
        ``cg-cellprofiler`` conda environment in standard locations, then
        falls back to the ``CELLPROFILER_PYTHON`` environment variable.

    Raises
    ------
    CellProfilerNotFoundError
        If no usable CellProfiler Python interpreter can be found.  See
        :doc:`/setup/cellprofiler` for setup instructions.

    Examples
    --------
    Measure a single cell at 0° rotation:

    >>> from cellgenerator import Image
    >>> from cellgenerator.mask import EllipseMask
    >>> from cellgenerator.stain import ConstantStain
    >>> from cellgenerator.measure import CellProfilerMeasurer
    >>> img = Image(dim=(500, 500), mask=EllipseMask(150, 80), stain=ConstantStain())
    >>> measurer = CellProfilerMeasurer()          # doctest: +SKIP
    >>> df = measurer.measure(img, dim=(200, 200)) # doctest: +SKIP
    >>> df.shape[1] > 100                          # doctest: +SKIP
    True

    Sweep rotations to study feature sensitivity:

    >>> import pandas as pd                        # doctest: +SKIP
    >>> rows = [
    ...     measurer.measure(img, dim=(200, 200), rotate=float(a))
    ...     for a in range(0, 360, 10)
    ... ]                                          # doctest: +SKIP
    >>> results = pd.concat(rows, ignore_index=True) # doctest: +SKIP
    """

    def __init__(self, python: str | Path | None = None) -> None:
        self._python = self._resolve_python(python)
        self._verify_environment()

    # ------------------------------------------------------------------
    # Environment discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_python(python: str | Path | None) -> Path:
        """Return the Path to the CellProfiler Python interpreter.

        Priority order:
        1. Explicit ``python`` argument
        2. ``CELLPROFILER_PYTHON`` environment variable
        3. Standard conda env locations for ``cg-cellprofiler``
        4. Current interpreter (if CellProfiler happens to be installed)
        """
        # Explicit argument
        if python is not None:
            p = Path(python).expanduser()
            if not p.exists():
                raise CellProfilerNotFoundError(
                    f"Provided python path does not exist: {p}"
                )
            return p

        # Environment variable
        env_var = os.environ.get("CELLPROFILER_PYTHON")
        if env_var:
            p = Path(env_var).expanduser()
            if p.exists():
                return p
            raise CellProfilerNotFoundError(
                f"CELLPROFILER_PYTHON is set to '{env_var}' "
                "but the file does not exist."
            )

        # Search standard conda locations
        for candidate in _CANDIDATE_PYTHONS:
            if candidate.exists():
                return candidate

        # Fall back to the current interpreter
        return Path(sys.executable)

    def _verify_environment(self) -> None:
        """Run ``_runner.py --check`` to confirm CellProfiler is importable."""
        try:
            result = subprocess.run(
                [str(self._python), str(_RUNNER), "--check"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise CellProfilerNotFoundError(
                f"Python interpreter not found: {self._python}\n{_SETUP_HINT}"
            )
        except subprocess.TimeoutExpired:
            raise CellProfilerNotFoundError(
                "Timed out waiting for CellProfiler to import.  "
                "The environment may be incomplete."
            )

        if result.returncode != 0:
            raise CellProfilerNotFoundError(
                f"CellProfiler import failed in '{self._python}'.\n"
                f"stderr: {result.stderr.strip()}\n"
                f"{_SETUP_HINT}"
            )

        try:
            info = json.loads(result.stdout)
            cp_ver = info.get("cellprofiler", "unknown")
            sys.stderr.write(
                f"[CellProfilerMeasurer] Using CellProfiler {cp_ver} "
                f"via {self._python}\n"
            )
        except json.JSONDecodeError:
            pass  # version info is informational only

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def measure(
        self,
        image: Image,
        dim: tuple[int, int],
        rotate: float = 0.0,
    ) -> pd.DataFrame:
        """Extract all CellProfiler features from *image* at *rotate* degrees.

        The intensity image and the ground-truth mask are rendered at ``dim``
        resolution, written to a temporary directory, and passed to the
        CellProfiler runner.  Results are returned as a single-row
        :class:`pandas.DataFrame` whose columns are CellProfiler feature names.

        Parameters
        ----------
        image : Image
            The synthetic cell to measure.
        dim : tuple[int, int]
            Output image size as ``(width, height)`` in pixels passed to
            :meth:`Image.get_img` and :meth:`Image.get_mask_img`.
        rotate : float, optional
            Clockwise rotation in degrees, by default ``0.0``.

        Returns
        -------
        pandas.DataFrame
            Single-row DataFrame.  Columns are CellProfiler feature names
            (e.g. ``AreaShape_Area``, ``Intensity_MeanIntensity_CellImage``).
            An additional ``rotate_deg`` column records the rotation angle.

        Raises
        ------
        RuntimeError
            If the CellProfiler runner subprocess exits with a non-zero code.
        """
        rotate = float(rotate)

        with tempfile.TemporaryDirectory(prefix="cg_cp_") as tmpdir:
            img_path = Path(tmpdir) / "cell.png"
            mask_path = Path(tmpdir) / "mask.png"

            # Render and save intensity image + label mask
            image.get_img(dim, rotate).save(str(img_path), "PNG")
            image.get_mask_img(dim, rotate).save(str(mask_path), "PNG")

            result = subprocess.run(
                [
                    str(self._python),
                    str(_RUNNER),
                    "--image",
                    str(img_path),
                    "--mask",
                    str(mask_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"CellProfiler runner failed (exit {result.returncode}).\n"
                f"stderr: {result.stderr.strip()}"
            )

        payload = json.loads(result.stdout)
        features: dict[str, float] = payload.get("features", {})
        errors: dict[str, str] = payload.get("errors", {})

        if errors:
            for module_name, tb in errors.items():
                sys.stderr.write(
                    f"[CellProfilerMeasurer] Module {module_name} reported an error:\n"
                    f"{tb}\n"
                )

        # Build a single-row DataFrame; prepend the rotation angle
        row = {"rotate_deg": rotate, **features}
        return pd.DataFrame([row])

    def measure_sweep(
        self,
        image: Image,
        dim: tuple[int, int],
        angles: list[float] | None = None,
    ) -> pd.DataFrame:
        """Measure features across multiple rotation angles.

        Convenience wrapper around :meth:`measure` that concatenates results
        into a single tidy DataFrame, one row per angle.

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

    @property
    def python(self) -> Path:
        """Path to the CellProfiler Python interpreter being used."""
        return self._python


# ---------------------------------------------------------------------------
# Setup hint shown in errors
# ---------------------------------------------------------------------------

_SETUP_HINT = """
To set up the CellProfiler environment, run:

    conda env create -f environment.yml

Then either:
  • Set the CELLPROFILER_PYTHON environment variable:
        export CELLPROFILER_PYTHON="$HOME/miniconda3/envs/cg-cellprofiler/bin/python"
  • Or pass the path explicitly:
        CellProfilerMeasurer(python="$HOME/miniconda3/envs/cg-cellprofiler/bin/python")

See docs/setup/cellprofiler.md for full instructions.
"""
