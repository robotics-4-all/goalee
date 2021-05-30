import math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Point:
    x: Optional[float] = 0.0
    y: Optional[float] = 0.0
    z: Optional[float] = 0.0

    def __sub__(self, other: Any):
        if isinstance(other, Point):
            return Point(self.x - other.x,
                         self.y - other.y,
                         self.z - other.z)
        elif isinstance(other, (float, int)):
            return Point(self.x - other,
                         self.y - other,
                         self.z - other)
        else:
            raise ValueError(
                f'Cannot perform substraction Point with type {type(other)}')

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x,
                         self.y + other.y,
                         self.z + other.z)
        elif isinstance(other, (float, int)):
            return Point(self.x + other,
                         self.y + other,
                         self.z + other)
        else:
            raise ValueError(
                f'Cannot perform addition of Point with type {type(other)}')

    def abs(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass
class Orientation:
    x: Optional[float] = 0.0
    y: Optional[float] = 0.0
    z: Optional[float] = 0.0

    def __sub__(self, other):
        if isinstance(other, Orientation):
            return Orientation(self.x - other.x,
                               self.y - other.y,
                               self.z - other.z)
        elif isinstance(other, (float, int)):
            return Orientation(self.x - other,
                               self.y - other,
                               self.z - other)
        else:
            raise ValueError(
                f'Cannot perform substraction Point with type {type(other)}')

    def __add__(self, other):
        if isinstance(other, Orientation):
            return Orientation(self.x + other.x,
                               self.y + other.y,
                               self.z + other.z)
        elif isinstance(other, (float, int)):
            return Orientation(self.x + other,
                               self.y + other,
                               self.z + other)
        else:
            raise ValueError(
                f'Cannot perform addition of Point with type {type(other)}')


@dataclass
class Pose:
    translation: Point
    orientation: Orientation
