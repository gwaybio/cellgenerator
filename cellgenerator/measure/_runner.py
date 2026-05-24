#!/usr/bin/env python3
"""CellProfiler feature extraction runner.

This script is designed to be executed **inside the CellProfiler conda
environment** (``cg-cellprofiler``).  cellgenerator invokes it as a
subprocess, passing pre-saved intensity and mask images.  Results are
written as JSON to stdout so the parent process can parse them.

Usage
-----
Verify the environment::

    python _runner.py --check

Extract features::

    python _runner.py --image cell.png --mask mask.png

The mask image must be a uint8 PNG where 0 = background and 1 = cell.
The intensity image must be an 8-bit grayscale PNG.
"""

import argparse
import json
import sys
import traceback

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMAGE_NAME = "CellImage"
OBJECT_NAME = "Cell"


# ---------------------------------------------------------------------------
# CellProfiler workspace helpers
# ---------------------------------------------------------------------------


def _set_headless() -> None:
    """Configure CellProfiler for headless (no-GUI) operation."""
    from cellprofiler_core.preferences import set_headless  # type: ignore[import]

    set_headless()


def _build_workspace(img_array, label_array):
    """Construct a minimal CellProfiler workspace from numpy arrays.

    Parameters
    ----------
    img_array : np.ndarray
        2-D float array in [0, 1] — the cell intensity image.
    label_array : np.ndarray
        2-D int array — 0 = background, 1 = cell object.

    Returns
    -------
    tuple[Workspace, Measurements]
    """
    import numpy as np
    from cellprofiler_core.image import Image as CPImage  # type: ignore[import]
    from cellprofiler_core.image import ImageSetList
    from cellprofiler_core.measurement import Measurements
    from cellprofiler_core.object import Objects, ObjectSet
    from cellprofiler_core.pipeline import Pipeline
    from cellprofiler_core.workspace import Workspace

    pipeline = Pipeline()
    measurements = Measurements()
    image_set_list = ImageSetList()
    image_set = image_set_list.get_image_set(0)
    object_set = ObjectSet()

    # Add the intensity image (CellProfiler expects float in [0, 1])
    cp_image = CPImage(pixel_data=img_array.astype(np.float64), convert=False)
    image_set.add(IMAGE_NAME, cp_image)

    # Add the pre-computed segmentation as a CellProfiler Objects instance
    objects = Objects()
    objects.segmented = label_array.astype(np.int32)
    object_set.add_objects(objects, OBJECT_NAME)

    workspace = Workspace(
        pipeline, None, image_set, object_set, measurements, image_set_list
    )
    return workspace, measurements


# ---------------------------------------------------------------------------
# Per-module measurement runners
# ---------------------------------------------------------------------------


def _run_size_shape(workspace, module_num: int) -> None:
    from cellprofiler.modules.measureobjectsizeshape import (  # type: ignore[import]
        MeasureObjectSizeShape,
    )

    m = MeasureObjectSizeShape()
    m.module_num = module_num
    m.objects_list.value = OBJECT_NAME
    m.calculate_zernikes.value = True
    m.run(workspace)


def _run_intensity(workspace, module_num: int) -> None:
    from cellprofiler.modules.measureobjectintensity import (  # type: ignore[import]
        MeasureObjectIntensity,
    )

    m = MeasureObjectIntensity()
    m.module_num = module_num
    m.images_list.value = IMAGE_NAME
    m.objects_list.value = OBJECT_NAME
    m.run(workspace)


def _run_texture(workspace, module_num: int) -> None:
    from cellprofiler.modules.measuretexture import (
        MeasureTexture,  # type: ignore[import]
    )

    m = MeasureTexture()
    m.module_num = module_num
    m.images_list.value = IMAGE_NAME
    m.objects_list.value = OBJECT_NAME
    # Default scales (3, 5, 10) — keep defaults
    m.run(workspace)


def _run_granularity(workspace, module_num: int) -> None:
    from cellprofiler.modules.measuregranularity import (  # type: ignore[import]
        MeasureGranularity,
    )

    m = MeasureGranularity()
    m.module_num = module_num
    m.images_list.value = IMAGE_NAME
    m.objects_list.value = OBJECT_NAME
    m.run(workspace)


def _run_radial_distribution(workspace, module_num: int) -> None:
    from cellprofiler.modules.measureobjectintensitydistribution import (  # type: ignore[import]
        MeasureObjectIntensityDistribution,
    )

    m = MeasureObjectIntensityDistribution()
    m.module_num = module_num
    m.images_list.value = IMAGE_NAME
    m.objects_list.value = OBJECT_NAME
    m.wants_zernikes.value = "Zernikes only"
    m.zernike_degree.value = 9
    m.run(workspace)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

_MODULES = [
    ("MeasureObjectSizeShape", _run_size_shape),
    ("MeasureObjectIntensity", _run_intensity),
    ("MeasureTexture", _run_texture),
    ("MeasureGranularity", _run_granularity),
    ("MeasureObjectRadialDistribution", _run_radial_distribution),
]


def _extract_features(measurements) -> dict[str, float]:
    """Pull all numeric per-object features out of the Measurements store."""
    import numpy as np

    features: dict[str, float] = {}
    for feature_name in measurements.get_feature_names(OBJECT_NAME):
        try:
            values = measurements.get_measurement(OBJECT_NAME, feature_name)
            if values is None or len(values) == 0:
                continue
            val = values[0]
            if isinstance(val, (int, float, np.integer, np.floating)) and not (
                isinstance(val, float) and (val != val)  # NaN check
            ):
                features[feature_name] = float(val)
        except Exception:
            pass  # silently skip unreadable features
    return features


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_check() -> None:
    """Verify that CellProfiler imports correctly and print version info."""
    import cellprofiler  # type: ignore[import]
    import cellprofiler_core  # type: ignore[import]

    print(
        json.dumps(
            {
                "status": "ok",
                "cellprofiler": cellprofiler.__version__,
                "cellprofiler_core": cellprofiler_core.__version__,
            }
        )
    )


def run_measure(image_path: str, mask_path: str) -> None:
    """Load images, run all measurement modules, print JSON features."""
    import numpy as np
    from PIL import Image as PILImage  # type: ignore[import]

    # Load arrays
    img_arr = np.array(PILImage.open(image_path).convert("L")).astype(np.float64)
    img_arr /= 255.0  # CellProfiler expects [0, 1]

    mask_arr = np.array(PILImage.open(mask_path).convert("L"))  # values 0 or 1

    _set_headless()
    workspace, measurements = _build_workspace(img_arr, mask_arr)

    errors: dict[str, str] = {}
    for module_num, (name, runner_fn) in enumerate(_MODULES, start=1):
        try:
            runner_fn(workspace, module_num)
        except Exception as exc:
            errors[name] = traceback.format_exc()
            sys.stderr.write(f"[cellprofiler_runner] WARNING: {name} failed: {exc}\n")

    features = _extract_features(measurements)
    print(json.dumps({"features": features, "errors": errors}))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CellProfiler feature extraction runner for cellgenerator"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify CellProfiler is importable and print version, then exit.",
    )
    parser.add_argument("--image", help="Path to the intensity image PNG.")
    parser.add_argument("--mask", help="Path to the label mask PNG (0=bg, 1=cell).")

    args = parser.parse_args()

    if args.check:
        run_check()
        return

    if not args.image or not args.mask:
        parser.error("--image and --mask are required unless --check is given.")

    run_measure(args.image, args.mask)


if __name__ == "__main__":
    main()
