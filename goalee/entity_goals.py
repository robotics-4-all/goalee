from typing import Any, Optional, Callable, List

import time
import uuid

from goalee.goal import Goal, GoalState
from goalee.entity import Entity


class EntityStateChange(Goal):

    def __init__(self,
                 entity: Entity,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__([entity],
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self.entity = entity
        self._last_state = self.entity.attributes.copy()

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def tick(self):
        if self._last_state != self.entity.attributes:
            self.set_state(GoalState.COMPLETED)
        self._last_state = self.entity.attributes.copy()


class EntityStateCondition(Goal):

    def __init__(self,
                 entities: List[Entity],
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 condition: Optional[Callable] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._condition = condition

    def get_entities_map(self):
        return {e.name: e for e in self._entities}

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def tick(self):
        try:
            if self._condition(self.get_entities_map()):
                self.set_state(GoalState.COMPLETED)
        except TypeError:
            pass
