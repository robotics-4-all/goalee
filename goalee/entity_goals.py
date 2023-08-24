from typing import Any, Optional, Callable, List
from enum import IntEnum

import time
import uuid

from commlib.node import Node

from goalee.goal import Goal, GoalState
from goalee.entity import Entity


class EntityStateChange(Goal):

    def __init__(self,
                 entity: Entity,
                 name: str = "",
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self.entities = [entity]
        self._last_state = self.entities[0].attributes.copy()

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def tick(self):
        if self._last_state != self.entities[0].attributes:
            self.set_state(GoalState.COMPLETED)
        self._last_state = self.entities[0].attributes.copy()


class EntityStateCondition(Goal):

    def __init__(self,
                 entities: List[Entity],
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 condition: Optional[Callable] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self.entities = entities
        self._msg = None
        self._condition = condition

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def tick(self):
        if self._condition(msg):
            self.set_state(GoalState.COMPLETED)
