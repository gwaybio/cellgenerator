"""Noise classes for multiplicative pixel-level perturbation."""

from ._abcnoise import AbstractNoise
from ._const_noise import ConstantNoise

__all__ = ["AbstractNoise", "ConstantNoise"]
