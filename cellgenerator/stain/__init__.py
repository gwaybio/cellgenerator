"""Stain classes defining intensity patterns within a cell."""

from ._abcstain import AbstractStain
from ._constant_stain import ConstantStain
from ._spatial_stain import SpatialStain

__all__ = ["AbstractStain", "ConstantStain", "SpatialStain"]
