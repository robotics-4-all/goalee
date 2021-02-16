from typing import Any, Optional, Callable
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures._base import TimeoutError
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
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 algorithm: Optional[ComplexGoalAlgorithm] = None,
                 accomplished: Optional[int] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._goals = []
        if algorithm is None:
            algorithm = ComplexGoalAlgorithm.ALL_ACCOMPLISHED
        self._algorithm = algorithm
        self._x_accomplished = accomplished

    def on_enter(self):
        if self._algorithm in (ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED,
                               ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED):
            self.run_seq()
        else:
            self.run_concurrent()
        print(f'Finished Complex Goal in {self._algorithm} Mode ({self._name})')
        self.calc_result()

    def run_seq(self):
        ## TODO: Timeout due to maxtime
        for g in self._goals:
            g.enter()

    def run_concurrent(self):
        n_threads = len(self._goals)
        features = []
        results = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            feature = executor.submit(goal.enter, )
            features.append(feature)
        # try:
        #     for f in as_completed(features, timeout=self._max_duration):
        #         results.append(f.result())
        # except TimeoutError as e:
        #     pass
        try:
            results = [future.result() for future in as_completed(features)]
        except TimeoutError as e:
            pass
        executor.shutdown(wait=False, cancel_futures=True)

    def calc_result(self):
        res_list = []
        for goal in self._goals:
            if goal._state == GoalState.COMPLETED:
                res_list.append(1)
            else:
                res_list.append(0)
        print(f'Complex Goal <{self._name}> Result List: {res_list}')
        completed = res_list.count(1)
        failed = res_list.count(0)

        if self._algorithm == ComplexGoalAlgorithm.ALL_ACCOMPLISHED:
            if completed == len(res_list):
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)
        elif self._algorithm == ComplexGoalAlgorithm.NONE_ACCOMPLISHED:
            if completed == 0:
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)
        elif self._algorithm == ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISED:
            if completed > 0:
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)
        elif self._algorithm == ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED:
            if completed == self._x_accomplished:
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)
        elif self._algorithm == ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED:
            if completed == len(res_list):
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)
        elif self._algorithm == \
            ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED:
            if completed == self._x_accomplished:
                self.set_state(GoalState.COMPLETED)
            else:
                self.set_state(GoalState.FAILED)

    def on_exit(self):
        pass

    def add_goal(self, goal: Goal):
        """add_goal
        Append goal.
        """
        if goal._max_duration is None:
            goal._max_duration = self._max_duration
        elif goal._max_duration > self._max_duration:
            goal._max_duration = self._max_duration
        if goal._min_duration is None:
            goal._min_duration = self._min_duration
        elif goal._min_duration > self._min_duration:
            goal._min_duration = self._min_duration
        self._goals.append(goal)

    def set_comm_node(self, comm_node: Node):
        super().set_comm_node(comm_node)
        for goal in self._goals:
            goal.set_comm_node(self._comm_node)
