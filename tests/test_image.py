"""Tests for the Image class."""

import numpy as np
import pytest
from PIL import Image as PILImage

from cellgenerator import Image
from cellgenerator.mask import CircleMask, EllipseMask
from cellgenerator.stain import ConstantStain

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_image():
    """A deterministic Image with constant stain — no randomness."""
    return Image(
        dim=(200, 200),
        mask=CircleMask(radius=80),
        stain=ConstantStain(),
    )


@pytest.fixture
def ellipse_image():
    return Image(
        dim=(500, 500),
        mask=EllipseMask(y_radius=150, x_radius=80),
        stain=ConstantStain(),
    )


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------


class TestImageConstruction:
    def test_valid_construction(self, simple_image):
        assert simple_image is not None

    def test_dim_not_tuple_raises(self):
        with pytest.raises((TypeError, ValueError)):
            Image(dim=[200, 200], mask=CircleMask(50), stain=ConstantStain())

    def test_dim_wrong_length_raises(self):
        with pytest.raises((TypeError, ValueError)):
            Image(dim=(200,), mask=CircleMask(50), stain=ConstantStain())

    def test_dim_float_entries_raise(self):
        with pytest.raises(TypeError):
            Image(dim=(200.0, 200.0), mask=CircleMask(50), stain=ConstantStain())

    def test_invalid_mask_raises(self):
        with pytest.raises(TypeError):
            Image(dim=(200, 200), mask="circle", stain=ConstantStain())

    def test_invalid_stain_raises(self):
        with pytest.raises(TypeError):
            Image(dim=(200, 200), mask=CircleMask(50), stain="flat")

    def test_invalid_noise_raises(self):
        with pytest.raises(TypeError):
            Image(
                dim=(200, 200), mask=CircleMask(50), stain=ConstantStain(), noise="none"
            )

    def test_stain_min_above_max_raises(self):
        with pytest.raises(ValueError):
            Image(
                dim=(200, 200),
                mask=CircleMask(50),
                stain=ConstantStain(),
                stain_min=0.9,
                stain_max=0.5,
            )

    def test_stain_min_zero_raises(self):
        with pytest.raises(ValueError):
            Image(
                dim=(200, 200),
                mask=CircleMask(50),
                stain=ConstantStain(),
                stain_min=0.0,
            )


# ---------------------------------------------------------------------------
# get_img output properties
# ---------------------------------------------------------------------------


class TestGetImg:
    def test_returns_pil_image(self, simple_image):
        result = simple_image.get_img(dim=(80, 80))
        assert isinstance(result, PILImage.Image)

    def test_output_size(self, simple_image):
        result = simple_image.get_img(dim=(64, 32))
        assert result.size == (64, 32)

    def test_output_mode_is_grayscale(self, simple_image):
        result = simple_image.get_img(dim=(80, 80))
        assert result.mode == "L"

    def test_pixel_range(self, simple_image):
        arr = np.array(simple_image.get_img(dim=(80, 80)))
        assert arr.min() >= 0
        assert arr.max() <= 255

    def test_idempotent_repeated_calls(self, simple_image):
        """Calling get_img twice must produce identical results (mutation bug check)."""
        img1 = np.array(simple_image.get_img(dim=(80, 80), rotate=0))
        img2 = np.array(simple_image.get_img(dim=(80, 80), rotate=0))
        np.testing.assert_array_equal(img1, img2)

    def test_invalid_dim_raises(self, simple_image):
        with pytest.raises((TypeError, ValueError)):
            simple_image.get_img(dim=(80,))

    def test_float_rotate_accepted(self, simple_image):
        img = simple_image.get_img(dim=(80, 80), rotate=45.0)
        assert isinstance(img, PILImage.Image)

    def test_int_rotate_accepted(self, simple_image):
        img = simple_image.get_img(dim=(80, 80), rotate=45)
        assert isinstance(img, PILImage.Image)


# ---------------------------------------------------------------------------
# Rotation properties (core scientific concern)
# ---------------------------------------------------------------------------


class TestRotationProperties:
    def test_mask_pixel_count_stable_across_rotations(self, simple_image):
        """Total bright-pixel count should be roughly stable under rotation.

        We use a circle + constant stain so only rotation affects the image.
        Exact pixel counts will differ slightly at edges due to interpolation.
        """
        counts = [
            np.array(simple_image.get_img(dim=(100, 100), rotate=angle)).sum()
            for angle in range(0, 360, 45)
        ]
        counts = np.array(counts, dtype=float)
        # Allow up to 5% relative variation due to PIL interpolation at edges
        assert counts.std() / counts.mean() < 0.05

    def test_rotation_changes_image(self, ellipse_image):
        """Rotating an ellipse by 90° should produce a measurably different image."""
        img_0 = np.array(ellipse_image.get_img(dim=(100, 100), rotate=0))
        img_90 = np.array(ellipse_image.get_img(dim=(100, 100), rotate=90))
        assert not np.array_equal(img_0, img_90)

    def test_full_rotation_returns_to_start(self, simple_image):
        """360° rotation should produce the same image as 0° (circle)."""
        img_0 = np.array(simple_image.get_img(dim=(100, 100), rotate=0))
        img_360 = np.array(simple_image.get_img(dim=(100, 100), rotate=360))
        np.testing.assert_array_equal(img_0, img_360)


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------


class TestSave:
    def test_save_creates_file(self, simple_image, tmp_path):
        out = tmp_path / "cell.png"
        simple_image.save(str(out), dim=(64, 64))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_saved_file_is_valid_image(self, simple_image, tmp_path):
        out = tmp_path / "cell.png"
        simple_image.save(str(out), dim=(64, 64))
        loaded = PILImage.open(str(out))
        assert loaded.size == (64, 64)
        assert loaded.mode == "L"

    def test_invalid_path_raises(self, simple_image):
        with pytest.raises(ValueError):
            simple_image.save(123, dim=(64, 64))
