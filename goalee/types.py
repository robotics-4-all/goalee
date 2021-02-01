from typing import Any, Dict, List, Optional

from dataclasses import dataclass


@dataclass
class Point:
    x: Optional[float] = 0.0
    y: Optional[float] = 0.0
    z: Optional[float] = 0.0
