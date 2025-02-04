import numpy as np
from typing import Tuple

from ._abcmask import _AbstractMask

class EllipseMask(_AbstractMask):
    def __init__(self, y_radius: float, x_radius: float) -> None:
        if isinstance(y_radius, int): y_radius = float(y_radius)
        if not isinstance(y_radius, float): raise TypeError("y_radius should be a float")
        if y_radius <= 0: raise ValueError("y_radius should be positive")
        if isinstance(x_radius, int): x_radius = float(x_radius)
        if not isinstance(x_radius, float): raise TypeError("x_radius should be a float")
        if x_radius <= 0: raise ValueError("x_radius should be positive")
        self._y_radius = y_radius
        self._x_radius = x_radius
    
    def _generate_mask(self, dim: Tuple[int, int]) -> np.ndarray:
        if not isinstance(dim, tuple): raise TypeError("dim should be a tuple")
        if len(dim) != 2: raise ValueError("dim should be of length 2")
        if not all([isinstance(entry, int) for entry in dim]): raise TypeError("All entries of dim should be integers")
        y, x = np.ogrid[:dim[0], :dim[1]]
        center_y, center_x = dim[0] / 2, dim[1] / 2
        distance_from_center = np.sqrt(((x - center_x) ** 2 / self._x_radius ** 2) + ((y - center_y) ** 2 / self._y_radius ** 2))
        mask = distance_from_center <= 1
        return mask
