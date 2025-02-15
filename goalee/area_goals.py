from typing import Any, List, Optional, Callable
from enum import IntEnum

import time
import uuid
import math

from commlib.node import Node

from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.types import Point
from goalee.logging import default_logger as logger


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
                 for_duration: Optional[float] = None,
                 tick_interval: Optional[float] = 0.1):
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration,
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
        self.log_info(
            f'Starting RectangleAreaGoal <{self._name}> with params:\n'
            f'-> Monitoring Entities: {self._entities}\n'
            f'-> Bottom Left Edge: {self._bottom_left_edge}\n'
            f'-> Length X: {self._length_x}\n'
            f'-> Length Y: {self._length_y}\n'
            f'-> Strategy: {self._tag.name}'
        )

    def on_exit(self):
        pass

    def check_area(self):
        for _last_state in self._last_states:
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
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.COMPLETED)
            elif reached and self.tag == AreaGoalTag.AVOID:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.FAILED)
            else:
                self._ts_hold = -1.0

    def tick(self):
        self._last_states = [entity.attributes.copy() for entity in self._entities]
        self.check_area()


class CircularAreaGoal(Goal):

    def __init__(self,
                 entities: List[Entity],
                 center: Point,
                 radius: float,
                 tag: AreaGoalTag = AreaGoalTag.ENTER,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None,
                 tick_interval: Optional[float] = 0.1):
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration,
                         tick_freq=int(1.0 / tick_interval))
        self._center = center
        self._radius = radius
        self._tag = tag
        self._last_states = [entity.attributes.copy() for entity in self._entities]

    @property
    def tag(self):
        return self._tag

    def on_exit(self):
        pass

    def on_enter(self):
        self.log_info(
            f'Starting CircularAreaGoal <{self._name}> with params:\n'
            f'-> Monitoring Entities: {[e.name for e in self._entities]}\n'
            f'-> Center: {self._center}\n'
            f'-> Radius: {self._radius}\n'
            f'-> Strategy: {self._tag.name}'
        )

    def check_area(self):
        for _last_state in self._last_states:
            if _last_state.get('position', None) is None:
                continue
            pos = _last_state['position']
            if pos['x'] == None or pos['y'] == None:
                continue
            dist = self._calc_distance(pos)
            reached = dist <= self._radius
            if reached and self.tag == AreaGoalTag.ENTER:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.COMPLETED)
            elif reached and self.tag == AreaGoalTag.AVOID:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.FAILED)
            else:
                self._ts_hold = -1.0

    def _calc_distance(self, pos):
        d = math.sqrt(
            (pos['x'] - self._center.x)**2 + \
            (pos['y'] - self._center.y)**2
        )
        return d

    def tick(self):
        self._last_states = [entity.attributes.copy() for entity in self._entities]
        self.check_area()


class MovingAreaGoal(Goal):

    def __init__(self,
                 motion_entity: Entity,
                 entities: List[Entity],
                 radius: float,
                 tag: AreaGoalTag = AreaGoalTag.ENTER,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None,
                 tick_interval: Optional[float] = 0.1):
        """
        Initializes an AreaGoal instance.

        Args:
            motion_entity (Entity): The entity that is in motion.
            entities (List[Entity]): A list of entities involved in the area goal.
            radius (float): The radius defining the area goal.
            tag (AreaGoalTag, optional): The tag indicating the type of area goal. Defaults to AreaGoalTag.ENTER.
            name (Optional[str], optional): The name of the area goal. Defaults to None.
            event_emitter (Optional[Any], optional): The event emitter for the area goal. Defaults to None.
            max_duration (Optional[float], optional): The maximum duration for the area goal. Defaults to None.
            min_duration (Optional[float], optional): The minimum duration for the area goal. Defaults to None.
        """
        self._mentity = motion_entity
        entities.remove(motion_entity) if motion_entity in entities else None
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration,
                         tick_freq=int(1.0 / tick_interval))
        self._radius = radius
        self._tag = tag
        self._last_states = [entity.state for entity in self._entities]

    @property
    def motion_entity(self):
        return self._mentity

    @property
    def tag(self):
        return self._tag

    def on_exit(self):
        pass

    def on_enter(self):
        self.log_info("Starting CircularAreaGoal <{}> with params:\n"
                    "-> Motion Entity: {}\n"
                    "-> Monitoring Entities: {}\n"
                    "-> Radius: {}\n"
                    "-> Strategy: {}".format(
                        self._name,
                        self._mentity,
                        [e.name for e in self._entities],
                        self._radius,
                        self._tag.name
                    ))

    def check_area(self):
        if self._mentity.state in (None, {}):
            return
        for _last_state in self._last_states:
            if _last_state in (None, {}):
                continue
            elif _last_state.get('position', None) is None:
                self.log_warning(f'Entity {_last_state} has no position attribute')
                continue
            pos = _last_state['position']
            if pos['x'] == None or pos['y'] == None:
                self.log_warning(f'Entity {_last_state}.position has no "x" or "y" attribute')
                continue
            dist = self._calc_distance(pos)
            reached = dist <= self._radius
            if reached and self.tag == AreaGoalTag.ENTER:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.COMPLETED)
            elif not reached and self.tag == AreaGoalTag.AVOID:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.FAILED)
            else:
                self._ts_hold = -1.0

    def _calc_distance(self, pos):
        d = math.sqrt(
            (pos['x'] - self._mentity.state["position"]["x"])**2 + \
            (pos['y'] - self._mentity.state["position"]["y"])**2
        )
        return d

    def tick(self):
        self._last_states = [entity.state for entity in self._entities]
        self.check_area()
