from typing import Any, Optional, Callable
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures._base import TimeoutError
import time
import uuid

from commlib.node import Node
from goalee.goal import Goal, GoalState
from goalee.logging import default_logger as logger
from goalee.rtmonitor import RTMonitor


class ComplexGoalAlgorithm(IntEnum):
    ALL_ACCOMPLISHED = 0
    ALL_ACCOMPLISHED_ORDERED = 1
    NONE_ACCOMPLISHED = 2
    AT_LEAST_ONE_ACCOMPLISHED = 3
    EXACTLY_X_ACCOMPLISHED = 4
    EXACTLY_X_ACCOMPLISHED_ORDERED = 5


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

    def set_tick_freq(self, freq: int):
        for goal in self._goals:
            goal.set_tick_freq(freq)

    def enter(self, rtmonitor: RTMonitor = None):
        self.set_state(GoalState.RUNNING)
        self.on_enter()

        elapsed = self.get_current_elapsed()
        if self._state == GoalState.FAILED:
            pass
        elif self._min_duration not in (None, 0) and elapsed < self._min_duration:
            self.set_state(GoalState.FAILED)
        elif self._algorithm not in (ComplexGoalAlgorithm.NONE_ACCOMPLISHED,
                                   ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED,
                                   ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED):
            if self._max_duration not in (None, 0) and elapsed > self._max_duration:
                self.set_state(GoalState.FAILED)

        self.on_exit()
        return self

    def on_enter(self):
        self.log_info(f'Starting ComplexGoal <{self._name}>:\n'
                      f"Parameters:\n"
                      f"  Algorithm: {self._algorithm.name}\n"
                      f"  X-Accomplished: {self._x_accomplished}\n"
                      f"  Max Duration: {self._max_duration}\n"
                      f"  Min Duration: {self._min_duration}\n"
                      f"Internal Goals: {[f'{g.__class__.__name__}:{g.name}' for g in self._goals]}")
        self._ts_start = self.get_current_ts()

        if self._algorithm in (ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED,
                               ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED):
            self.run_seq()
        else:
            self.run_concurrent()

        self.calc_result()

        self.log_info(
            f'Finished ComplexGoal <{self.__class__.__name__}:{self._name}>\n'
            f'  Mode {self._algorithm.name}\n'
            f'  Results: {self._get_results_list()}'
        )

    def run_seq(self):
        for g in self._goals:
            g.enter()
            if self._max_duration is not None and self.get_current_elapsed() > self._max_duration:
                self.set_state(GoalState.FAILED)
                break

    def run_concurrent(self):
        """
        Executes the 'enter' method of each goal in self._goals concurrently using a thread pool.

        This method creates a thread pool with a number of threads equal to the number of goals.
        Each goal's 'enter' method is submitted to the thread pool for execution. The results
        of the 'enter' methods are collected and returned once all threads have completed.

        If a TimeoutError occurs during the execution, it is caught and ignored.

        The thread pool is shut down after all tasks are completed or if an exception occurs.
        """
        n_threads = len(self._goals)
        futures = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            future = executor.submit(goal.enter)
            futures.append(future)
        try:
            for f in as_completed(futures, timeout=self._max_duration):
                try:
                    goal = f.result()
                    if goal.state == GoalState.COMPLETED and \
                        self._algorithm == ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISHED:
                        self.log_info(f"Goal <ComplexGoal:{goal.name}> reached at least one accomplished")
                        self.terminate_all_goals()
                        break
                except Exception as e:
                    self.log_error(f"Error in goal execution: {e}")
        except TimeoutError:
            pass
        executor.shutdown(wait=False, cancel_futures=True)

    def terminate(self):
        self.terminate_all_goals()
        return super().terminate()

    def terminate_all_goals(self):
        for goal in self._goals:
            if goal.state not in (GoalState.COMPLETED, GoalState.FAILED, GoalState.TERMINATED):
                goal.terminate()

    def calc_result(self):
        res_list = self._get_results_list()
        self.log_info(f'<{self.__class__.__name__}:{self._name}> results: {res_list}')
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
        elif self._algorithm == ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISHED:
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

    def add_goal(self, goal: Goal):
        if (goal._max_duration is None or goal._max_duration > self._max_duration) and self._max_duration is not None:
            goal._max_duration = self._max_duration
            self.log_info(f'Goal <{goal.__class__.__name__}:{goal.name}> max duration set to {self._max_duration}')
        if (goal._min_duration is None or goal._min_duration < self._min_duration) and self._min_duration is not None:
            goal._min_duration = self._min_duration
            self.log_info(f'Goal <{goal.__class__.__name__}:{goal.name}> min duration set to {self._min_duration}')
        self._goals.append(goal)

    def set_comm_node(self, comm_node: Node):
        super().set_comm_node(comm_node)
        for goal in self._goals:
            goal.set_comm_node(self._comm_node)

    def reset(self):
        self.set_state(GoalState.IDLE)
        self._ts_start = -1.0
        self._ts_exit = -1.0
        self._ts_hold = -1.0
        self._duration = -1.0
        for goal in self._goals:
            goal.reset()
        self.on_reset()
