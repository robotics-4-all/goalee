from typing import Any, List, Optional
from enum import IntEnum

import time
import uuid

from goalee.entity import Entity


class GoalState(IntEnum):
    IDLE = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3


class Goal():

    def __init__(self,
                 entities: Optional[List[Entity]],
                 event_emitter: Optional[Any] = None,
                 name: Optional[str] = None,
                 tick_freq: Optional[int] = 10,  # hz
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        self._status = 0
        self._ee = event_emitter
        self._max_duration = max_duration
        self._min_duration = min_duration
        if name in (None, ""):
            name = self._gen_random_name()
        self._name = name
        self._freq = tick_freq
        self._entities = entities
        self.set_state(GoalState.IDLE)

    @property
    def entities(self):
        return self._entities

    @property
    def name(self):
        return self._name

    @property
    def status(self):
        return self._status

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
        print(f'Goal <{self._name}> entered {state_str} state ' +
              f'(maxT={self._max_duration}, minT={self._min_duration})')

    def enter(self):
        print(f'Entering Goal <{self._name}:{self.__class__.__name__}>')
        self.set_state(GoalState.RUNNING)
        self.on_enter()
        self.run_until_exit()
        status = 1 if self.state == GoalState.COMPLETED else 0
        print(f'Goal <{self._name}:{self.__class__.__name__}>' + \
              f' exited with status: {self.state}')
        self._status = status
        return self.state

    def on_enter(self):
        pass

    def tick(self):
        pass

    def run_until_exit(self):
        ts_start = time.time()
        while self._state not in (GoalState.COMPLETED, GoalState.FAILED):
            self.tick()
            elapsed = time.time() - ts_start
            if self._max_duration in (None, 0):
                continue
            elif elapsed > self._max_duration:
                self.set_state(GoalState.FAILED)
                print(
                    f'Goal <{self._name}> exited due' + \
                    f' to timeout after {self._max_duration} seconds!')
            time.sleep(1 / self._freq)
        elapsed = time.time() - ts_start
        if self._min_duration not in  (None, 0):
            if elapsed < self._min_duration:
                self.set_state(GoalState.FAILED)
        self.on_exit()

    def on_exit(self):
        raise NotImplementedError("on_exit is not implemented")

    def _gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')
