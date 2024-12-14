from typing import Any, Optional, Callable
from enum import IntEnum

import time
import uuid
import math

from commlib.node import Node

from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.types import Point, Orientation


class PoseGoal(Goal):

    def __init__(self,
                 entity: Entity,
                 position: Point,
                 orientation: Orientation,
                 deviation_pos: float = 0.0,
                 deviation_ori: float = 0.0,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__([entity], event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._entity = entity
        self._position = position
        self._orientation = orientation
        self._deviation_pos = deviation_pos
        self._deviation_ori = deviation_ori

    def on_enter(self):
        print(f'Starting PoseGoal <{self._name}> with params:')
        print(f'-> Entity: {self._entity}')

    def on_exit(self):
        pass

    def check_pose(self):
        if self._last_state.get('position', None) is None:
            return
        pos = self._last_state['position']
        if pos.get('x', 'None') is None or pos.get('y', 'None') is None:
            return
        reached =  pos > (self._position - self._deviation_pos) and \
            pos < (self._position + self._deviation_pos) and \
            ori > (self._orientation - self._deviation_ori) and \
            ori < (self._orientation + self._deviation_ori)
        if reached:
            self.set_state(GoalState.COMPLETED)

    def tick(self):
        self._last_state = self._entity.attributes.copy()
        self.check_pose()

class PositionGoal(Goal):

    def __init__(self,
                 topic: str,
                 position: Point,
                 deviation: float = 0.0,
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
        self._position = position
        self._deviation = deviation

    def on_enter(self):
        print(f'Starting PoseGoal <{self._name}> with params:')
        print(f'-> topic: {self._topic}')
        self._listener = self._comm_node.create_subscriber(
            topic=self._topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        pos = msg['position']
        if pos > (self._position - self._deviation) and \
                pos < (self._position + self._deviation):
            self.set_state(GoalState.COMPLETED)


class OrientationGoal(Goal):

    def __init__(self,
                 topic: str,
                 orientation: Orientation,
                 deviation: float = 0.0,
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
        self._orientation = orientation
        self._deviation = deviation

    def on_enter(self):
        print(f'Starting OrientationGoal <{self._name}> with params:')
        print(f'-> topic: {self._topic}')
        self._listener = self._comm_node.create_subscriber(
            topic=self._topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        ori = msg['orientation']
        if ori > (self._orientation - self._deviation) and \
                ori < (self._orientation + self._deviation):
            self.set_state(GoalState.COMPLETED)
