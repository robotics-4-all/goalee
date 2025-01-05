from typing import Any, Optional, Callable
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures._base import TimeoutError
import time
import uuid

from commlib.node import Node
from goalee.goal import Goal, GoalState
from goalee.logging import default_logger as logger


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
                 min_duration: Optional[float] = None,
                 *args, **kwargs):
        super().__init__(comm_node,
                         event_emitter,
                         name=name,
                         max_duration=max_duration,
                         min_duration=min_duration,
                         *args, **kwargs)
        self._goals = []
        if algorithm is None:
            algorithm = ComplexGoalAlgorithm.ALL_ACCOMPLISHED
        self._algorithm = algorithm
        self._x_accomplished = accomplished

    @property
    def goals(self):
        return self._goals

    def on_enter(self):
        if self._algorithm in (ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED,
                               ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED):
            self.run_seq()
        else:
            self.run_concurrent()
        logger.info(f'Finished <{self.__class__.__name__}:{self.name}> - Mode {self._algorithm.name}')
        self.calc_result()

    def run_seq(self):
        ## TODO: Timeout due to maxtime
        for g in self._goals:
            g.enter()

    def run_concurrent(self):
        n_threads = len(self._goals)
        features = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            feature = executor.submit(goal.enter, )
            features.append(feature)
        try:
            results = [future.result() for future in as_completed(features)]
        except TimeoutError:
            pass
        executor.shutdown(wait=False, cancel_futures=True)

    def calc_result(self):
        res_list = self._get_results_list()
        logger.info(f'<{self.__class__.__name__}:{self._name}> results: {res_list}')
        completed = res_list.count(1)
        # failed = res_list.count(0)
        self._evaluate_results(completed, res_list)

    def _get_results_list(self):
        res_list = []
        for goal in self._goals:
            if goal._state == GoalState.COMPLETED:
                res_list.append(1)
            else:
                res_list.append(0)
        return res_list

    def _evaluate_results(self, completed, res_list):
        if self._algorithm == ComplexGoalAlgorithm.ALL_ACCOMPLISHED:
            self._set_state_all_accomplished(completed, res_list)
        elif self._algorithm == ComplexGoalAlgorithm.NONE_ACCOMPLISHED:
            self._set_state_none_accomplished(completed)
        elif self._algorithm == ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISED:
            self._set_state_at_least_one_accomplished(completed)
        elif self._algorithm == ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED:
            self._set_state_exactly_x_accomplished(completed)
        elif self._algorithm == ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED:
            self._set_state_all_accomplished(completed, res_list)
        elif self._algorithm == ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED:
            self._set_state_exactly_x_accomplished(completed)

    def _set_state_all_accomplished(self, completed, res_list):
        if completed == len(res_list):
            self.set_state(GoalState.COMPLETED)
        else:
            self.set_state(GoalState.FAILED)

    def _set_state_none_accomplished(self, completed):
        if completed == 0:
            self.set_state(GoalState.COMPLETED)
        else:
            self.set_state(GoalState.FAILED)

    def _set_state_at_least_one_accomplished(self, completed):
        if completed > 0:
            self.set_state(GoalState.COMPLETED)
        else:
            self.set_state(GoalState.FAILED)

    def _set_state_exactly_x_accomplished(self, completed):
        if completed == self._x_accomplished:
            self.set_state(GoalState.COMPLETED)
        else:
            self.set_state(GoalState.FAILED)

    def on_exit(self):
        pass

    def add_goal(self, goal: Goal):
        if (goal._max_duration is None or goal._max_duration > self._max_duration) and self._max_duration is not None:
            goal._max_duration = self._max_duration
            logger.info(f'Goal <{goal.__class__.__name__}:{goal.name}> max duration set to {self._max_duration}')
        if (goal._min_duration is None or goal._min_duration < self._min_duration) and self._min_duration is not None:
            goal._min_duration = self._min_duration
            logger.info(f'Goal <{goal.__class__.__name__}:{goal.name}> min duration set to {self._min_duration}')
        self._goals.append(goal)

    def set_comm_node(self, comm_node: Node):
        super().set_comm_node(comm_node)
        for goal in self._goals:
            goal.set_comm_node(self._comm_node)
