from abc import ABCMeta, abstractmethod
from typing import Any, Optional
from enum import IntEnum

import time
import uuid

from commlib.node import Node


class GoalState(IntEnum):
    IDLE = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3


class Goal(metaclass=ABCMeta):

    def __init__(self,
                 comm_node: Node,
                 event_emitter: Optional[Any] = None,
                 name: Optional[str] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        self._comm_node = comm_node
        self._ee = event_emitter
        self._max_duration = max_duration
        self._min_duration = min_duration
        if name is None:
            name = self._gen_random_name()
        self._name = name
        self.set_state(GoalState.IDLE)

    @property
    def state(self):
        return self._state

    def set_state(self, state: GoalState):
        if state not in GoalState:
            raise ValueError('Not a valid state was given')
        self._state = state
        self._report_state()

    def _report_state(self):
        if self._state == GoalState.IDLE:
            state_str  = 'IDLE'
        elif self._state == GoalState.RUNNING:
            state_str  = 'RUNNING'
        elif self._state == GoalState.COMPLETED:
            state_str  = 'COMPLETED'
        elif self._state == GoalState.FAILED:
            state_str  = 'FAILED'
        print(f'[*] - Goal <{self._name}> entered {state_str} state ' +
              f'(maxT={self._max_duration}, minT={self._min_duration})')

    def enter(self):
        print(f'[*] - Entering Goal <{self._name}:{self.__class__.__name__}>')
        self.set_state(GoalState.RUNNING)
        self.on_enter()
        self.run_until_exit()
        return self.state

    @abstractmethod
    def on_enter(self):
        pass

    def run_until_exit(self):
        ts_start = time.time()
        while self._state not in (GoalState.COMPLETED, GoalState.FAILED):
            time.sleep(0.001)
            elapsed = time.time() - ts_start
            if self._max_duration in (None, 0):
                continue
            elif elapsed > self._max_duration:
                self.set_state(GoalState.FAILED)
                print(
                    f'[*] - Goal <{self._name}> exited due' + \
                    f' to timeout after {self._max_duration} seconds!')
        elapsed = time.time() - ts_start
        if self._min_duration not in  (None, 0):
            if elapsed < self._min_duration:
                self.set_state(GoalState.FAILED)
        self.on_exit()

    @abstractmethod
    def on_exit(self):
        pass

    def set_comm_node(self, comm_node: Node):
        if not isinstance(comm_node, Node):
            raise ValueError('')
        self._comm_node = comm_node

    def _gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')
