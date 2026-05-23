"""Tests for noise classes."""

import numpy as np
import pytest

from cellgenerator.noise import ConstantNoise

IMG = np.full((50, 50), 0.5)


class TestConstantNoise:
    def test_add_noise_returns_same_values(self):
        result = ConstantNoise()._add_noise(IMG)
        np.testing.assert_allclose(result, IMG)

    def test_generate_noise_returns_ones(self):
        noise = ConstantNoise()._generate_noise(IMG)
        np.testing.assert_array_equal(noise, np.ones_like(IMG))

    def test_output_shape_preserved(self):
        result = ConstantNoise()._add_noise(IMG)
        assert result.shape == IMG.shape

    def test_clipping_applied(self):
        """Values above 1 should be clipped."""
        bright = np.full((10, 10), 2.0)
        result = ConstantNoise()._add_noise(bright)
        assert result.max() <= 1.0

    def test_non_array_raises(self):
        with pytest.raises(TypeError):
            ConstantNoise()._add_noise([[0.5, 0.5], [0.5, 0.5]])

    def test_3d_array_raises(self):
        with pytest.raises(ValueError):
            ConstantNoise()._add_noise(np.zeros((10, 10, 3)))
