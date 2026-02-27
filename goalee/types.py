from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class Point:
    x: float | None = 0.0
    y: float | None = 0.0
    z: float | None = 0.0

    def __sub__(self, other: Any):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, (float, int)):
            return Point(self.x - other, self.y - other, self.z - other)
        else:
            raise ValueError(
                f"Cannot perform substraction Point with type {type(other)}"
            )

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y and self.z == other.z
        if isinstance(other, dict):
            return (
                self.x == other["x"] and self.y == other["y"] and self.z == other["z"]
            )
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
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        elif isinstance(other, (float, int)):
            return Point(self.x + other, self.y + other, self.z + other)
        else:
            raise ValueError(
                f"Cannot perform addition of Point with type {type(other)}"
            )


@dataclass
class Orientation:
    roll: float | None = 0.0
    pitch: float | None = 0.0
    yaw: float | None = 0.0

    def __init__(
        self,
        roll: float | None = 0.0,
        pitch: float | None = 0.0,
        yaw: float | None = 0.0,
        *,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ) -> None:
        # Accept x/y/z as aliases for roll/pitch/yaw (robotics convention).
        # If both are provided, the explicit roll/pitch/yaw take precedence
        # only when they differ from the default (0.0).
        self.roll = x if x is not None and roll == 0.0 else roll
        self.pitch = y if y is not None and pitch == 0.0 else pitch
        self.yaw = z if z is not None and yaw == 0.0 else yaw

    def __sub__(self, other):
        if isinstance(other, Orientation):
            return Orientation(
                self.roll - other.roll, self.pitch - other.pitch, self.yaw - other.yaw
            )
        elif isinstance(other, (float, int)):
            return Orientation(self.roll - other, self.pitch - other, self.yaw - other)
        else:
            raise ValueError(
                f"Cannot perform substraction Point with type {type(other)}"
            )

    def __eq__(self, other):
        if isinstance(other, Orientation):
            return (
                self.roll == other.roll
                and self.pitch == other.pitch
                and self.yaw == other.yaw
            )
        elif isinstance(other, (dict)):
            return (
                self.roll == other["roll"]
                and self.pitch == other["pitch"]
                and self.yaw == other["yaw"]
            )
        return False

    def abs(self):
        return math.sqrt(self.roll**2 + self.pitch**2 + self.yaw**2)

    def __add__(self, other):
        if isinstance(other, Orientation):
            return Orientation(
                self.roll + other.roll, self.pitch + other.pitch, self.yaw + other.yaw
            )
        elif isinstance(other, (float, int)):
            return Orientation(self.roll + other, self.pitch + other, self.yaw + other)
        else:
            raise ValueError(
                f"Cannot perform addition of Point with type {type(other)}"
            )

    def __gt__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) > (
                other.roll,
                other.pitch,
                other.yaw,
            )
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) > (
                other["roll"],
                other["pitch"],
                other["yaw"],
            )
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) >= (
                other.roll,
                other.pitch,
                other.yaw,
            )
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) >= (
                other["roll"],
                other["pitch"],
                other["yaw"],
            )
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) < (
                other.roll,
                other.pitch,
                other.yaw,
            )
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) < (
                other["roll"],
                other["pitch"],
                other["yaw"],
            )
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Orientation):
            return (self.roll, self.pitch, self.yaw) <= (
                other.roll,
                other.pitch,
                other.yaw,
            )
        elif isinstance(other, (dict)):
            return (self.roll, self.pitch, self.yaw) <= (
                other["roll"],
                other["pitch"],
                other["yaw"],
            )


@dataclass
class Pose:
    translation: Point
    orientation: Orientation
