from typing import Any, List, Optional
from enum import IntEnum

import time
import uuid

from goalee.entity import Entity
from goalee.logging import default_logger as logger


class GoalState(IntEnum):
    IDLE = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3


class Goal():

    def __init__(self,
                 entities: Optional[List[Entity]] = None,
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
        self._entities = entities if entities is not None else []
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
        logger.info(f'Goal <{self.name}> entered {state_str} state ' +
              f'(maxT={self._max_duration}, minT={self._min_duration})')

    def enter(self):
        """
        Enter the goal, set its state to RUNNING, and execute it until it exits.

        This method performs the following steps:
        1. Logs the entry into the goal.
        2. Sets the goal's state to RUNNING.
        3. Calls the on_enter() method.
        4. Runs the goal until it exits.
        5. Determines the status based on the goal's final state.
        6. Logs the exit status of the goal.
        7. Sets the internal status attribute based on the goal's final state.
        8. Returns the final state of the goal.

        Returns:
            GoalState: The final state of the goal after execution.
        """
        logger.info(f'Entering Goal <{self.name}>')
        self.set_state(GoalState.RUNNING)
        self.on_enter()
        self.run_until_exit()
        status = 1 if self.state == GoalState.COMPLETED else 0
        logger.info(f'Goal <{self.name}>' + \
              f' exited with status: {self.state}')
        self._status = status
        return self.state

    def on_enter(self):
        raise NotImplementedError("on_enter is not implemented")

    def tick(self):
        raise NotImplementedError("tick is not implemented")

    def run_until_exit(self):
        """
        Runs the goal until it reaches a terminal state (COMPLETED or FAILED) or exceeds the maximum duration.

        This method repeatedly calls the `tick` method to progress the goal's state. It checks the elapsed time
        to determine if the goal has exceeded its maximum allowed duration, in which case it sets the state to FAILED.
        If the goal completes or fails, it calls the `on_exit` method.

        The method also ensures that the goal runs for at least the minimum duration specified. If the goal completes
        before the minimum duration, it sets the state to FAILED.

        Attributes:
            ts_start (float): The timestamp when the method starts running.
            elapsed (float): The time elapsed since the method started running.

        Raises:
            None

        Notes:
            - The method sleeps for a duration determined by the frequency (`self._freq`) between each tick.
            - The goal's state is checked against `GoalState.COMPLETED` and `GoalState.FAILED` to determine if it should exit.
            - If `_max_duration` is None or 0, the goal can run indefinitely until it reaches a terminal state.
            - If `_min_duration` is None or 0, there is no minimum duration constraint for the goal.
        """
        ts_start = time.time()
        while self._state not in (GoalState.COMPLETED, GoalState.FAILED):
            self.tick()
            elapsed = time.time() - ts_start
            if self._max_duration in (None, 0):
                continue
            elif elapsed > self._max_duration:
                self.set_state(GoalState.FAILED)
                logger.info(
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
