from typing import Any, List, Optional, Callable
from enum import IntEnum

import time
import uuid
import math

from commlib.node import Node

from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.types import Point


class AreaGoalTag(IntEnum):
    ENTER = 0
    EXIT =  1
    AVOID = 2
    STEP =  3


class RectangleAreaGoal(Goal):

    def __init__(self,
                 entities: List[Entity],
                 bottom_left_edge: Point,
                 length_x: float,
                 length_y: float,
                 tag: AreaGoalTag = AreaGoalTag.ENTER,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 tick_interval: Optional[float] = 1):
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         tick_freq=int(1.0 / tick_interval))
        self._bottom_left_edge = bottom_left_edge
        self._length_x = length_x
        self._length_y = length_y
        self._tag = tag
        self._last_states = [entity.attributes.copy() for entity in self._entities]

    @property
    def tag(self):
        return self._tag

    def on_enter(self):
        print(f'Starting RectangleAreaGoal <{self._name}> with params:')
        print(f'-> Entities: {self._entities}')
        print(f'-> bottom_left_edge: {self._bottom_left_edge}')
        print(f'-> length_x: {self._length_x}')
        print(f'-> length_y: {self._length_y}')

    def on_exit(self):
        pass

    def run_for_entities(self):
        for _last_state in self._last_states:
            print(_last_state)
            if _last_state.get('position', None) is None:
                continue
            pos = _last_state['position']
            if pos['x'] == None or pos['y'] == None:
                continue
            x_axis = (pos['x'] < (self._bottom_left_edge.x + self._length_x)
                    and pos['x'] > self._bottom_left_edge.x)
            y_axis = (pos['y'] < (self._bottom_left_edge.y + self._length_y)
                    and pos['y'] > self._bottom_left_edge.y)
            reached = x_axis and y_axis
            if reached and self.tag == AreaGoalTag.ENTER:
                self.set_state(GoalState.COMPLETED)
            elif not reached and self.tag == AreaGoalTag.AVOID:
                self.set_state(GoalState.FAILED)

    def tick(self):
        print('Ticking...')
        self._last_states = [entity.attributes.copy() for entity in self._entities]
        self.run_for_entities()


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
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._topic = topic
        self._msg = None
        self._center = center
        self._radius = radius
        self._tag = tag

    @property
    def tag(self):
        return self._tag

    def on_enter(self):
        print(f'Starting CircularAreaGoal <{self._name}> with params:')
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
