from typing import Any, Optional

from commlib.node import Node

from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.types import Point, Orientation
from goalee.logging import default_logger as logger


class PoseGoal(Goal):

    def __init__(self,
                 entity: Entity,
                 position: Point,
                 orientation: Orientation,
                 deviation_pos: float = 0.0,
                 deviation_ori: float = 0.0,
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
        self.log_info(
            f'Starting PoseGoal <{self._name}> with params:\n'
            f'-> Entity: {self._entity.name}\n'
            f'-> Position: {self._position}\n'
            f'-> Orientation: {self._orientation}\n'
            f'-> Deviation Position: {self._deviation_pos}\n'
            f'-> Deviation Orientation: {self._deviation_ori}'
        )

    def on_exit(self):
        pass

    def check_pose(self):
        if self._last_state.get('position', None) is None:
            return
        pos = self._last_state['position']
        if pos.get('x', 'None') is None or pos.get('y', 'None') is None:
            return
        if self._last_state.get('orientation', None) is None:
            return
        ori = self._last_state['orientation']
        if ori.get('x', 'None') is None or ori.get('y', 'None') is None:
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
                 entity: Entity,
                 position: Point,
                 deviation: float = 0.0,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__([entity], event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._entity = entity
        self._position = position
        self._deviation = deviation

    def on_enter(self):
        self.log_info(
            f'Starting PositionGoal <{self._name}> with params:\n'
            f'-> Entity: {self._entity.name}\n'
            f'-> Position: {self._position}\n'
            f'-> Deviation: {self._deviation}\n'
            f'-> Max Duration: {self._max_duration}\n'
            f'-> Min Duration: {self._min_duration}'
        )

    def on_exit(self):
        pass

    def check_pos(self):
        if self._last_state.get('position', None) is None:
            return
        pos = self._last_state['position']
        if pos.get('x', 'None') is None or pos.get('y', 'None') is None:
            return
        reached = pos > (self._position - self._deviation) and \
                pos < (self._position + self._deviation)
        if reached:
            self.set_state(GoalState.COMPLETED)

    def tick(self):
        self._last_state = self._entity.attributes.copy()
        self.check_pos()


class OrientationGoal(Goal):
    def __init__(self,
                 entity: Entity,
                 orientation: Orientation,
                 deviation: float = 0.0,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__([entity], event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._entity = entity
        self._orientation = orientation
        self._deviation = deviation

    def on_enter(self):
        self.log_info(
            f'Starting OrientationGoal <{self._name}> with params:\n'
            f'-> Entity: {self._entity.name}\n'
            f'-> Orientation: {self._orientation}\n'
            f'-> Deviation: {self._deviation}\n'
            f'-> Max Duration: {self._max_duration}\n'
            f'-> Min Duration: {self._min_duration}'
        )

    def on_exit(self):
        pass

    def check_ori(self):
        if self._last_state.get('orientation', None) is None:
            return
        ori = self._last_state['orientation']
        if ori.get('x', 'None') is None or ori.get('y', 'None') is None:
            return
        reached = ori > (self._orientation - self._deviation) and \
                ori < (self._orientation + self._deviation)
        if reached:
            self.set_state(GoalState.COMPLETED)

    def tick(self):
        self._last_state = self._entity.attributes.copy()
        self.check_ori()
