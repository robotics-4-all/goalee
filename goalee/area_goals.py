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
                 tick_interval: Optional[float] = 0.1):
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
        logger.info(f'Starting RectangleAreaGoal <{self._name}> with params:')
        logger.info(f'-> Monitoring Entities: {self._entities}')
        logger.info(f'-> Bottom Left Edge: {self._bottom_left_edge}')
        logger.info(f'-> Length X: {self._length_x}')
        logger.info(f'-> Length Y: {self._length_y}')
        logger.info(f'-> Strategy: {self._tag.name}')

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
                self.set_state(GoalState.COMPLETED)
            elif not reached and self.tag == AreaGoalTag.AVOID:
                self.set_state(GoalState.FAILED)

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
                 min_duration: Optional[float] = None):
        super().__init__(entities,event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
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
        logger.info(f'Starting CircularAreaGoal <{self._name}> with params:')
        logger.info(f'-> Monitoring Entities: {[e.name for e in self._entities]}')
        logger.info(f'-> Center: {self._center}')
        logger.info(f'-> Radius: {self._radius}')
        logger.info(f'-> Strategy: {self._tag.name}')

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
                # inside the circle
                self.set_state(GoalState.COMPLETED)
            elif not reached and self.tag == AreaGoalTag.AVOID:
                self.set_state(GoalState.FAILED)

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
                 min_duration: Optional[float] = None):
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
        super().__init__(entities,event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
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
        logger.info(f'Starting CircularAreaGoal <{self._name}> with params:')
        logger.info(f'-> Motion Entity: {self._mentity}')
        logger.info(f'-> Monitoring Entities: {[e.name for e in self._entities]}')
        logger.info(f'-> Radius: {self._radius}')
        logger.info(f'-> Strategy: {self._tag.name}')

    def check_area(self):
        if self._mentity.state in (None, {}):
            return
        for _last_state in self._last_states:
            if _last_state in (None, {}):
                continue
            elif _last_state.get('position', None) is None:
                logger.warning(f'Entity {_last_state} has no position attribute')
                continue
            pos = _last_state['position']
            if pos['x'] == None or pos['y'] == None:
                logger.warning(f'Entity {_last_state}.position has no "x" or "y" attribute')
                continue
            dist = self._calc_distance(pos)
            reached = dist <= self._radius
            if reached and self.tag == AreaGoalTag.ENTER:
                # inside the circle
                self.set_state(GoalState.COMPLETED)
            elif not reached and self.tag == AreaGoalTag.AVOID:
                self.set_state(GoalState.FAILED)

    def _calc_distance(self, pos):
        d = math.sqrt(
            (pos['x'] - self._mentity.state["position"]["x"])**2 + \
            (pos['y'] - self._mentity.state["position"]["y"])**2
        )
        return d

    def tick(self):
        self._last_states = [entity.state for entity in self._entities]
        self.check_area()
