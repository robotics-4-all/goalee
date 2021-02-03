from typing import Any, Optional, Callable
from enum import IntEnum

import time
import uuid
import math

from commlib.node import Node

from goalee.goal import Goal, GoalState
from goalee.types import Point


class AreaGoalTag(IntEnum):
    ENTER = 0
    EXIT =  1
    AVOID = 2
    STEP =  3


class RectangleAreaGoal(Goal):

    def __init__(self,
                 topic: str,
                 bottomLeftEdge: Point,
                 length_x: float,
                 length_y: float,
                 tag: AreaGoalTag = AreaGoalTag.ENTER,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration)
        self._topic = topic
        self._msg = None
        self._bottomLeftEdge = bottomLeftEdge
        self._length_x = length_x
        self._length_y = length_y
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def on_enter(self):
        print(f'[*] - Starting RectangleAreaGoal <{self._name}> with params:')
        print(f'-> topic: {self._topic}')
        print(f'-> bottomLeftEdge: {self._bottomLeftEdge}')
        print(f'-> length_x: {self._length_x}')
        print(f'-> length_y: {self._length_y}')
        self._listener = self._comm_node.create_subscriber(
            topic=self._topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        pos = msg['position']
        x_axis = (pos['x'] < (self._bottomLeftEdge.x + self._length_x)
                  and pos['x'] > self._bottomLeftEdge.x)
        y_axis = (pos['y'] < (self._bottomLeftEdge.y + self._length_y)
                  and pos['y'] > self._bottomLeftEdge.y)
        reached = x_axis and y_axis
        if reached and self.tag == AreaGoalTag.ENTER:
            self.set_state(GoalState.COMPLETED)


class CircularAreaGoal(Goal):

    def __init__(self,
                 topic: str,
                 center: Point,
                 radius: float,
                 tag: AreaGoalTag = AreaGoalTag.ENTER,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration)
        self._topic = topic
        self._msg = None
        self._center = center
        self._radius = radius
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def on_enter(self):
        print(f'[*] - Starting CircularAreaGoal <{self._name}> with params:')
        print(f'-> topic: {self._topic}')
        print(f'-> center: {self._center}')
        print(f'-> radius: {self._radius}')
        self._listener = self._comm_node.create_subscriber(
            topic=self._topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        pos = msg['position']
        dist = self._calc_distance(pos)
        if dist < self._radius and self.tag == AreaGoalTag.ENTER:
            # inside the circle
            self.set_state(GoalState.COMPLETED)

    def _calc_distance(self, pos):
        d = math.sqrt(
            (pos['x'] - self._center.x)**2 + \
            (pos['y'] - self._center.y)**2
        )
        return d
