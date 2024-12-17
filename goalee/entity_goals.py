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
            # print(type(self._condition))
            if callable(self._condition) and self._condition.__name__ == "<lambda>":
                cond_state = self._condition(self.get_entities_map())
            elif isinstance(self._condition, str):
                cond_state = self.evaluate_condition(self.get_entities_map())
            if cond_state:
                self.set_state(GoalState.COMPLETED)
        except TypeError:
            pass


    def evaluate_condition(self, entities):
        import statistics
        try:
            if eval(
                self._condition,
                {
                    'entities': entities
                },
                {
                    'std': statistics.stdev,
                    'var': statistics.variance,
                    'mean': statistics.mean,
                    'min': min,
                    'max': max,
                }
            ):
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
