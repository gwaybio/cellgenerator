"""Tests for the measure module.

CellProfiler-dependent tests are skipped automatically when the
``cg-cellprofiler`` conda environment is not configured.  The skip check
uses the ``CELLPROFILER_PYTHON`` env var or the standard conda env paths
that ``CellProfilerMeasurer`` itself searches.

Tests that do NOT require CellProfiler (mask rendering, DataFrame shape
contract, error path) run unconditionally.
"""

import numpy as np
import pandas as pd
import pytest
from PIL import Image as PILImage

from cellgenerator import Image
from cellgenerator.mask import CircleMask, EllipseMask
from cellgenerator.measure import CellProfilerMeasurer, CellProfilerNotFoundError
from cellgenerator.stain import ConstantStain

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

DIM = (200, 200)
OUT_DIM = (100, 100)


@pytest.fixture
def circle_img():
    """Deterministic Image: circle + constant stain."""
    return Image(dim=DIM, mask=CircleMask(radius=80), stain=ConstantStain())


@pytest.fixture
def ellipse_img():
    return Image(dim=(500, 500), mask=EllipseMask(150, 80), stain=ConstantStain())


# ---------------------------------------------------------------------------
# get_mask_img — no CellProfiler needed
# ---------------------------------------------------------------------------


class TestGetMaskImg:
    def test_returns_pil_image(self, circle_img):
        result = circle_img.get_mask_img(OUT_DIM)
        assert isinstance(result, PILImage.Image)

    def test_output_size(self, circle_img):
        result = circle_img.get_mask_img(dim=(64, 32))
        assert result.size == (64, 32)

    def test_mode_is_grayscale(self, circle_img):
        assert circle_img.get_mask_img(OUT_DIM).mode == "L"

    def test_only_binary_values(self, circle_img):
        arr = np.array(circle_img.get_mask_img(OUT_DIM))
        assert set(arr.flat).issubset({0, 1})

    def test_has_foreground_pixels(self, circle_img):
        arr = np.array(circle_img.get_mask_img(OUT_DIM))
        assert arr.sum() > 0

    def test_has_background_pixels(self, circle_img):
        arr = np.array(circle_img.get_mask_img(OUT_DIM))
        assert (arr == 0).sum() > 0

    def test_mask_aligns_with_intensity(self, circle_img):
        """Foreground pixels in mask should be bright in the intensity image."""
        intensity = np.array(circle_img.get_img(OUT_DIM))
        mask = np.array(circle_img.get_mask_img(OUT_DIM)).astype(bool)
        assert intensity[mask].mean() > intensity[~mask].mean()

    def test_rotation_changes_mask(self, ellipse_img):
        """Rotating an ellipse should shift which pixels are foreground."""
        m0 = np.array(ellipse_img.get_mask_img(OUT_DIM, rotate=0))
        m90 = np.array(ellipse_img.get_mask_img(OUT_DIM, rotate=90))
        assert not np.array_equal(m0, m90)

    def test_rotation_preserves_pixel_count(self, circle_img):
        """Circle mask pixel count should be stable under rotation."""
        counts = [
            np.array(circle_img.get_mask_img(OUT_DIM, rotate=float(a))).sum()
            for a in range(0, 360, 45)
        ]
        counts = np.array(counts, dtype=float)
        assert counts.std() / counts.mean() < 0.05

    def test_invalid_dim_raises(self, circle_img):
        with pytest.raises((TypeError, ValueError)):
            circle_img.get_mask_img(dim=(100,))

    def test_float_dim_raises(self, circle_img):
        with pytest.raises(TypeError):
            circle_img.get_mask_img(dim=(100.0, 100.0))


class TestSaveMask:
    def test_save_creates_file(self, circle_img, tmp_path):
        out = tmp_path / "mask.png"
        circle_img.save_mask(str(out), dim=OUT_DIM)
        assert out.exists() and out.stat().st_size > 0

    def test_saved_mask_is_binary(self, circle_img, tmp_path):
        out = tmp_path / "mask.png"
        circle_img.save_mask(str(out), dim=OUT_DIM)
        arr = np.array(PILImage.open(str(out)))
        assert set(arr.flat).issubset({0, 1})

    def test_invalid_path_raises(self, circle_img):
        with pytest.raises(ValueError):
            circle_img.save_mask(123, dim=OUT_DIM)


# ---------------------------------------------------------------------------
# CellProfilerMeasurer — skip if env not available
# ---------------------------------------------------------------------------


# This fixture attempts to build a measurer; if that raises
# CellProfilerNotFoundError the entire test class is skipped.
@pytest.fixture(scope="module")
def measurer():
    try:
        return CellProfilerMeasurer()
    except CellProfilerNotFoundError as exc:
        pytest.skip(f"CellProfiler environment not configured: {exc}")


class TestCellProfilerMeasurer:
    def test_measure_returns_dataframe(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        assert isinstance(df, pd.DataFrame)

    def test_measure_single_row(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        assert len(df) == 1

    def test_measure_has_rotate_column(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM, rotate=45.0)
        assert "rotate_deg" in df.columns
        assert df["rotate_deg"].iloc[0] == 45.0

    def test_measure_has_many_features(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        # Expect at least 50 CellProfiler features beyond rotate_deg
        assert df.shape[1] > 50

    def test_measure_area_shape_present(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        area_cols = [c for c in df.columns if "AreaShape" in c]
        assert len(area_cols) > 0

    def test_measure_intensity_present(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        intensity_cols = [c for c in df.columns if "Intensity" in c]
        assert len(intensity_cols) > 0

    def test_measure_texture_present(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        texture_cols = [c for c in df.columns if "Texture" in c]
        assert len(texture_cols) > 0

    def test_measure_all_numeric(self, measurer, circle_img):
        df = measurer.measure(circle_img, dim=OUT_DIM)
        non_numeric = [
            c
            for c in df.columns
            if c != "rotate_deg" and not pd.api.types.is_numeric_dtype(df[c])
        ]
        assert non_numeric == []

    def test_circle_area_shape_eccentricity_near_zero(self, measurer, circle_img):
        """A circle should have eccentricity close to 0."""
        df = measurer.measure(circle_img, dim=OUT_DIM)
        ecc_cols = [c for c in df.columns if "Eccentricity" in c]
        if ecc_cols:
            assert df[ecc_cols[0]].iloc[0] < 0.3

    def test_measure_sweep_returns_correct_rows(self, measurer, circle_img):
        angles = [0.0, 90.0, 180.0, 270.0]
        df = measurer.measure_sweep(circle_img, dim=OUT_DIM, angles=angles)
        assert len(df) == len(angles)
        assert list(df["rotate_deg"]) == angles

    def test_circle_features_stable_under_rotation(self, measurer, circle_img):
        """Circle AreaShape features should be ~constant across rotations."""
        df = measurer.measure_sweep(
            circle_img, dim=OUT_DIM, angles=[0.0, 45.0, 90.0, 135.0]
        )
        area_col = next((c for c in df.columns if c == "AreaShape_Area"), None)
        if area_col:
            cv = df[area_col].std() / df[area_col].mean()
            assert cv < 0.05, f"AreaShape_Area CV = {cv:.3f} (expected < 0.05)"


class TestCellProfilerMeasurerErrors:
    def test_bad_python_path_raises(self):
        with pytest.raises(CellProfilerNotFoundError):
            CellProfilerMeasurer(python="/nonexistent/python")
