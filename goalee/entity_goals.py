from enum import IntEnum
from typing import Any, Optional, Callable, List

import statistics
import math

from goalee.goal import Goal, GoalState
from goalee.entity import Entity


CONDITION_FUNCTIONS = {
    'std': statistics.stdev,
    'var': statistics.variance,
    'mean': statistics.mean,
    'min': min,
    'max': max,
    'fabs': math.fabs
}


class EntityStateChange(Goal):

    def __init__(self,
                 entity: Entity,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None):
        super().__init__([entity],
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration)
        self.entity = entity
        self._last_state = self.entity.attributes.copy()

    def on_enter(self):
        self.log_info(
            f"Starting EntityStateChange Goal <{self.name}>:\n"
            f"Entity: {self.entity.name}\n"
            f"Max Duration: {self._max_duration}\n"
            f"Min Duration: {self._min_duration}\n"
            f"For Duration: {self._for_duration}"
        )

    def tick(self):
        if self._last_state != self.entity.attributes:
            if self._for_duration is not None and self._for_duration > 0:
                self._ts_hold = self.get_current_ts()
            else:
                self.set_state(GoalState.COMPLETED)
        elif self._ts_hold is not None and self._for_duration is not None:
            if self.get_current_ts() - self._ts_hold > self._for_duration:
                self.set_state(GoalState.COMPLETED)
        self._last_state = self.entity.attributes.copy()


class EntityStateCondition(Goal):

    def __init__(self,
                 entities: List[Entity],
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 condition: Optional[Callable] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None):
        super().__init__(entities,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration)
        self._condition = condition

    def get_entities_map(self):
        return {e.name: e for e in self._entities}

    def on_enter(self):
        self.log_info(
            f"Starting EntityStateCondition Goal <{self.name}>:\n"
            f"Parameters:\n"
            f"  Condition: {self._condition}\n"
            f"  Max Duration: {self._max_duration}\n"
            f"  Min Duration: {self._min_duration}\n"
            f"  For Duration: {self._for_duration}"
        )
        self._ts_hold = -1.0

    def tick(self):
        """
        Evaluates the condition of the goal and updates its state accordingly.
        If the condition evaluates to True, the goal state is set to COMPLETED.

        Exceptions:
            - Catches and ignores TypeError exceptions.

        Raises:
            TypeError: If there is an issue with the type of the condition.
        """
        try:
            if isinstance(self._condition, type(lambda: None)):
                e = self.get_entities_map()
                cond_state = self._condition(e)
            elif callable(self._condition):
                cond_state = self._condition(self.get_entities_map())
            elif isinstance(self._condition, str):
                cond_state = self.evaluate_condition(self.get_entities_map())
            if cond_state:
                if self._for_duration is not None and self._for_duration > 0:
                    if self._ts_hold is None or self._ts_hold < 0:
                        self._ts_hold = self.get_current_ts()
                    elif self.get_current_ts() - self._ts_hold > self._for_duration:
                        self.set_state(GoalState.COMPLETED)
                else:
                    self.set_state(GoalState.COMPLETED)
            else:
                self._ts_hold = -1.0
        except TypeError as e:
            pass

    def evaluate_condition(self, entities):
        """
        Evaluates a condition based on the provided entities.

        This method uses the `eval` function to evaluate a condition stored in the
        instance variable `_condition`. The condition can use statistical functions
        such as standard deviation, variance, mean, min, and max, which are provided
        in the local scope for the evaluation.

        Args:
            entities (list): A list of entities to be used in the condition evaluation.

        Returns:
            bool: True if the condition evaluates to True, False otherwise. If an
                  exception occurs during evaluation, the method returns False.
        """
        try:
            if eval(
                self._condition,
                {
                    'entities': entities
                },
                CONDITION_FUNCTIONS
            ):
                return True
            else:
                return False
        except Exception as e:
            if "NoneType" in str(e):
                pass
            else:
                self.log_error(f"Error in condition evaluation: {e}")
            return False


class AttrStreamStrategy(IntEnum):
    ALL = 0
    NONE = 1
    AT_LEAST_ONE = 2
    JUST_ONE = 3
    EXACTLY_X = 4
    ALL_ORDERED = 5
    EXACTLY_X_ORDERED = 6


class EntityAttrStream(Goal):

    def __init__(self,
                 entity: List[Entity],
                 attr: str,
                 value: List[Any],
                 strategy: AttrStreamStrategy,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None):
        super().__init__([entity],
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         for_duration=for_duration)
        self._entity = entity
        self._attr = attr
        self._value = value
        self._strategy = strategy
        self._last_state = None

        self._value_check_list = [False] * len(self._value)

    def on_enter(self):
        self.log_info(
            f"Starting EntityAttrStream Goal <{self.name}>:\n"
            f"Attribute: {self._attr}\n"
            f"Value: {self._value}\n"
            f"Strategy: {self._strategy.name}\n"
            f"Max Duration: {self._max_duration}\n"
            f"Min Duration: {self._min_duration}"
        )

    def tick(self):
        _state = self._entity.attributes.copy()
        if self._last_state is None:
            self._last_state = _state
        elif _state[self._attr] == self._last_state[self._attr]:
            return

        self._last_state = _state

        if self._attr not in self._entity.attributes:
            raise ValueError(f"Attribute {self._attr} not found in entity {self._entity.name}")

        for i, v in enumerate(self._value):
            if self._value_check_list[i] == True:
                continue
            if self._last_state[self._attr] == v:
                self._value_check_list[i] = True
                if self._strategy in (AttrStreamStrategy.ALL_ORDERED,
                                      AttrStreamStrategy.EXACTLY_X_ORDERED):
                    self.process_for_ordered_strategy()
                    break

        if self.is_done():
            self.set_state(GoalState.COMPLETED)

    def is_done(self):
        if self._strategy == AttrStreamStrategy.ALL:
            return all(self._value_check_list)
        elif self._strategy == AttrStreamStrategy.NONE:
            return not any(self._value_check_list)
        elif self._strategy == AttrStreamStrategy.AT_LEAST_ONE:
            return any(self._value_check_list)
        elif self._strategy == AttrStreamStrategy.JUST_ONE:
            return sum(self._value_check_list) == 1
        elif self._strategy == AttrStreamStrategy.EXACTLY_X:
            return sum(self._value_check_list) == len(self._value)
        elif self._strategy == AttrStreamStrategy.ALL_ORDERED:
            return all(self._value_check_list)
        elif self._strategy == AttrStreamStrategy.EXACTLY_X_ORDERED:
            return sum(self._value_check_list) == len(self._value)

    def process_for_ordered_strategy(self):
        idx = next((i for i in reversed(range(len(self._value_check_list))) if self._value_check_list[i]), -1)
        if not all(self._value_check_list[:idx]):
            self.reset_check_list()

    # def process_for_ordered_strategy(self):
    #     self.log_info(f"Value check list: {self._value_check_list}")
    #     for i in range(len(self._value_check_list)-1):
    #         if self._value_check_list[i+1] and not self._value_check_list[i]:
    #             # self.reset_check_list()
    #             break

    def reset_check_list(self):
        self._value_check_list = [False] * len(self._value)
