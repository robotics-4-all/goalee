from typing import Any, Optional, Callable
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import uuid

from commlib.node import Node
from goalee.goal import Goal, GoalState


class ComplexGoalAlgorithm(IntEnum):
    ALL_ACCOMPLISHED = 0
    ALL_ACCOMPLISHED_ORDERED = 1
    NONE_ACCOMPLISHED = 2
    AT_LEAST_ONE_ACCOMPLISED = 3
    EXACTLY_X_ACCOMPLISHED = 4
    EXACTLY_X_ACCOMPLISHED_ORDERED = 4


class ComplexGoal(Goal):

    def __init__(self,
                 topic: str,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 algorithm: Optional[ComplexGoalAlgorithm] = None,
                 accomplished: Optional[int] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration)
        self._listening_topic = topic
        self._msg = None
        self._goals = []
        if algorithm is None:
            algorithm = ComplexGoalAlgorithm.ALL_ACCOMPLISHED
        self._algorithm = algorithm

    def on_enter(self):
        if self._algorithm in (ComplexGoalAlgorithm.ALL_ACCOMPLISHED,
                               ComplexGoalAlgorithm.NONE_ACCOMPLISHED,
                               ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED):
            self.run_seq()
        else:
            self.run_concurrent()
        print(f'[*] - Finished Complex Goal in {self._algorithm} Mode ({self._name})')

    def run_seq(self):
        for g in self._goals:
            g.enter()

    def run_concurrent(self):
        n_threads = len(self._goals)
        features = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            feature = executor.submit(goal.enter, )
            features.append(feature)
        for f in as_completed(features):
            pass

    def on_exit(self):
        pass

    def add_goal(self, goal: Goal):
        self._goals.append(goal)
