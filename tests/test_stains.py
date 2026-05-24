"""Tests for stain classes."""

import numpy as np
import pytest

from cellgenerator.stain import ConstantStain, SpatialStain

DIM = (100, 100)


# ---------------------------------------------------------------------------
# ConstantStain
# ---------------------------------------------------------------------------


class TestConstantStain:
    def test_output_shape(self):
        arr = ConstantStain()._generate_stain(DIM)
        assert arr.shape == DIM

    def test_default_value_is_one(self):
        arr = ConstantStain()._generate_stain(DIM)
        np.testing.assert_array_equal(arr, np.ones(DIM))

    def test_custom_const(self):
        arr = ConstantStain(const=0.7)._generate_stain(DIM)
        np.testing.assert_allclose(arr, np.full(DIM, 0.7))

    def test_zero_const_raises(self):
        with pytest.raises(ValueError):
            ConstantStain(const=0.0)

    def test_negative_const_raises(self):
        with pytest.raises(ValueError):
            ConstantStain(const=-0.5)

    def test_const_above_one_raises(self):
        with pytest.raises(ValueError):
            ConstantStain(const=1.1)

    def test_int_const_accepted(self):
        stain = ConstantStain(const=1)
        assert isinstance(stain._const, float)


# ---------------------------------------------------------------------------
# SpatialStain
# ---------------------------------------------------------------------------


class TestSpatialStain:
    def test_output_shape(self):
        arr = SpatialStain(y_corr=10, x_corr=10)._generate_stain(DIM)
        assert arr.shape == DIM

    def test_output_is_float(self):
        arr = SpatialStain(y_corr=10, x_corr=10)._generate_stain(DIM)
        assert np.issubdtype(arr.dtype, np.floating)

    def test_not_constant(self):
        """Spatially correlated noise should not be uniform."""
        arr = SpatialStain(y_corr=5, x_corr=5)._generate_stain((200, 200))
        assert arr.std() > 0

    def test_higher_correlation_smoother(self):
        """Larger sigma should produce lower pixel-to-pixel variance."""
        np.random.seed(42)
        rough = SpatialStain(y_corr=1, x_corr=1)._generate_stain((200, 200))
        smooth = SpatialStain(y_corr=30, x_corr=30)._generate_stain((200, 200))
        assert smooth.std() < rough.std()

    def test_zero_y_corr_raises(self):
        with pytest.raises(ValueError, match="positive"):
            SpatialStain(y_corr=0, x_corr=10)

    def test_zero_x_corr_raises(self):
        with pytest.raises(ValueError, match="positive"):
            SpatialStain(y_corr=10, x_corr=0)

    def test_stochastic(self):
        """Two calls without a fixed seed should differ."""
        s = SpatialStain(y_corr=5, x_corr=5)
        a1 = s._generate_stain(DIM)
        a2 = s._generate_stain(DIM)
        assert not np.array_equal(a1, a2)
