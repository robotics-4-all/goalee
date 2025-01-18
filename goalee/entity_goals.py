from typing import Any, Optional, Callable, List

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
        self.log_info(
            f"Starting EntityStateChange Goal <{self.name}>:\n"
            f"Entity: {self.entity.name}\n"
            f"Max Duration: {self._max_duration}\n"
            f"Min Duration: {self._min_duration}"
        )

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
        self.log_info(
            f"Starting EntityStateCondition Goal <{self.name}>:\n"
            f"Condition: {self._condition}\n"
            f"Max Duration: {self._max_duration}\n"
            f"Min Duration: {self._min_duration}"
        )

    def on_exit(self):
        pass

    def tick(self):
        """
        Evaluates the condition of the goal and updates its state accordingly.

        This method checks the type of the condition and evaluates it based on its type:
        - If the condition is a lambda function, it evaluates the lambda with the entities map.
        - If the condition is any callable, it evaluates the callable with the entities map.
        - If the condition is a string, it evaluates the condition as a string expression.

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
            if callable(self._condition):
                cond_state = self._condition(self.get_entities_map())
            elif isinstance(self._condition, str):
                cond_state = self.evaluate_condition(self.get_entities_map())
            if cond_state:
                self.set_state(GoalState.COMPLETED)
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
        except Exception:
            return False
