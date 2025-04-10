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

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y and self.z == other.z
        if isinstance(other, dict):
            return self.x == other["x"] and self.y == other["y"] and self.z == other["z"]
        return False

    def __lt__(self, other):
        if isinstance(other, Point):
            return (self.x, self.y, self.z) < (other.x, other.y, other.z)
        elif isinstance(other, (dict)):
            return (self.x, self.y, self.z) < (other["x"], other["y"], other["z"])
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Point):
            return (self.x, self.y, self.z) <= (other.x, other.y, other.z)
        elif isinstance(other, (dict)):
            return (self.x, self.y, self.z) <= (other["x"], other["y"], other["z"])
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Point):
            return (self.x, self.y, self.z) > (other.x, other.y, other.z)
        elif isinstance(other, (dict)):
            return (self.x, self.y, self.z) > (other["x"], other["y"], other["z"])
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Point):
            return (self.x, self.y, self.z) >= (other.x, other.y, other.z)
        elif isinstance(other, (dict)):
            return (self.x, self.y, self.z) >= (other["x"], other["y"], other["z"])
        return NotImplemented

    def abs(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

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


@dataclass
class Orientation:
    roll: Optional[float] = 0.0
    pitch: Optional[float] = 0.0
    yaw: Optional[float] = 0.0

    def __sub__(self, other):
        if isinstance(other, Orientation):
            return Orientation(self.roll - other.roll,
                               self.pitch - other.pitch,
                               self.yaw - other.yaw)
        elif isinstance(other, (float, int)):
            return Orientation(self.roll - other,
                               self.pitch - other,
                               self.yaw - other)
        else:
            raise ValueError(
                f'Cannot perform substraction Point with type {type(other)}')

    def __eq__(self, other):
        if isinstance(other, Orientation):
            return self.roll == other.roll and self.pitch == other.pitch and self.yaw == other.yaw
        elif isinstance(other, (dict)):
            return self.roll == other["roll"] and self.pitch == other["pitch"] and self.yaw == other["yaw"]
        return False

    def abs(self):
        return math.sqrt(self.roll**2 + self.pitch**2 + self.yaw**2)

    def __add__(self, other):
        if isinstance(other, Orientation):
            return Orientation(self.roll + other.roll,
                               self.pitch + other.pitch,
                               self.yaw + other.yaw)
        elif isinstance(other, (float, int)):
            return Orientation(self.roll + other,
                               self.pitch + other,
                               self.yaw + other)
        else:
            raise ValueError(
                f'Cannot perform addition of Point with type {type(other)}')

    def __gt__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) > (other.roll, other.pitch, other.yaw)
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) > (other["roll"], other["pitch"], other["yaw"])
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) >= (other.roll, other.pitch, other.yaw)
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) >= (other["roll"], other["pitch"], other["yaw"])
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) < (other.roll, other.pitch, other.yaw)
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) < (other["roll"], other["pitch"], other["yaw"])
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) <= (other.roll, other.pitch, other.yaw)
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) <= (other["roll"], other["pitch"], other["yaw"])

@dataclass
class Pose:
    translation: Point
    orientation: Orientation
