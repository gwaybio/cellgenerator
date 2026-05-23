"""Tests for mask classes."""

import numpy as np
import pytest

from cellgenerator.mask import CircleMask, EllipseMask

DIM = (200, 200)


# ---------------------------------------------------------------------------
# CircleMask
# ---------------------------------------------------------------------------


class TestCircleMask:
    def test_output_shape(self):
        mask = CircleMask(radius=50)
        arr = mask._generate_mask(DIM)
        assert arr.shape == DIM

    def test_output_dtype_is_bool(self):
        mask = CircleMask(radius=50)
        arr = mask._generate_mask(DIM)
        assert arr.dtype == bool

    def test_center_is_inside(self):
        mask = CircleMask(radius=50)
        arr = mask._generate_mask(DIM)
        cy, cx = DIM[0] // 2, DIM[1] // 2
        assert arr[cy, cx]

    def test_corners_are_outside(self):
        mask = CircleMask(radius=50)
        arr = mask._generate_mask(DIM)
        assert not arr[0, 0]
        assert not arr[0, -1]
        assert not arr[-1, 0]
        assert not arr[-1, -1]

    def test_radius_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            CircleMask(radius=0)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError, match="positive"):
            CircleMask(radius=-10)

    def test_int_radius_accepted(self):
        """Integer radius should be silently coerced to float."""
        mask = CircleMask(radius=50)
        assert isinstance(mask._radius, float)

    def test_larger_radius_more_pixels(self):
        small = CircleMask(radius=30)._generate_mask(DIM)
        large = CircleMask(radius=80)._generate_mask(DIM)
        assert large.sum() > small.sum()

    def test_invalid_dim_type_raises(self):
        mask = CircleMask(radius=50)
        with pytest.raises((TypeError, ValueError)):
            mask._generate_mask([200, 200])  # list, not tuple

    def test_invalid_dim_entries_raise(self):
        mask = CircleMask(radius=50)
        with pytest.raises(TypeError):
            mask._generate_mask((200.0, 200.0))


# ---------------------------------------------------------------------------
# EllipseMask
# ---------------------------------------------------------------------------


class TestEllipseMask:
    def test_output_shape(self):
        mask = EllipseMask(y_radius=80, x_radius=40)
        arr = mask._generate_mask(DIM)
        assert arr.shape == DIM

    def test_output_dtype_is_bool(self):
        mask = EllipseMask(y_radius=80, x_radius=40)
        arr = mask._generate_mask(DIM)
        assert arr.dtype == bool

    def test_center_is_inside(self):
        mask = EllipseMask(y_radius=80, x_radius=40)
        arr = mask._generate_mask(DIM)
        cy, cx = DIM[0] // 2, DIM[1] // 2
        assert arr[cy, cx]

    def test_asymmetry(self):
        """Tall ellipse should have more pixels in y span than x span."""
        mask = EllipseMask(y_radius=80, x_radius=20)
        arr = mask._generate_mask(DIM)
        cy, cx = DIM[0] // 2, DIM[1] // 2
        # Count how far the mask extends vertically vs horizontally from center
        y_extent = arr[:, cx].sum()
        x_extent = arr[cy, :].sum()
        assert y_extent > x_extent

    def test_zero_y_radius_raises(self):
        with pytest.raises(ValueError, match="positive"):
            EllipseMask(y_radius=0, x_radius=40)

    def test_zero_x_radius_raises(self):
        with pytest.raises(ValueError, match="positive"):
            EllipseMask(y_radius=80, x_radius=0)

    def test_circle_is_special_case(self):
        """Equal radii should produce the same mask as CircleMask."""
        r = 50.0
        ellipse = EllipseMask(y_radius=r, x_radius=r)._generate_mask(DIM)
        circle = CircleMask(radius=r)._generate_mask(DIM)
        np.testing.assert_array_equal(ellipse, circle)
