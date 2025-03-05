from typing import Any, List, Optional
from enum import IntEnum

import time
import uuid

from goalee.entity import Entity
from goalee.logging import default_logger as logger
from goalee.rtmonitor import RTMonitor, EventMsg


class GoalState(IntEnum):
    IDLE = 0  # Goal is not running
    RUNNING = 1  # Goal is currently running
    COMPLETED = 2  # Goal successfully achieved its objective
    FAILED = 3  # Goal failed to achieve its objective
    TERMINATED = 4  # Goal was terminated by an external event


class Goal:

    def __init__(self,
                 entities: Optional[List[Entity]] = None,
                 event_emitter: Optional[Any] = None,
                 name: Optional[str] = None,
                 tick_freq: Optional[int] = 10,  # hz
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None,
                 for_duration: Optional[float] = None):
        self._rtmonitor: RTMonitor = None
        self._state = None
        self._ee = event_emitter
        self._max_duration: float = max_duration
        self._min_duration: float = min_duration
        self._for_duration: float = for_duration
        self._duration: float = -1.0
        if name in (None, ""):
            name = self._gen_random_name()
        self._name: str = name
        self._freq: int = tick_freq
        self._entities: List = entities if entities is not None else []
        self._ts_start: float = -1.0
        self._ts_hold: float = -1.0
        self.set_state(GoalState.IDLE)

    def serialize(self):
        return {
            'name': self._name,
            'type': self.__class__.__name__,
            'state': self._state.name,
            'entities': [entity.name for entity in self._entities]
        }

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def entities(self) -> list:
        return self._entities

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> bool:
        return True if self.state == GoalState.COMPLETED else False

    @property
    def state(self) -> GoalState:
        return self._state

    def set_rtmonitor(self, rtmonitor):
        self._rtmonitor = rtmonitor

    def set_state(self, state: GoalState):
        """
        Sets the state of the goal.

        Args:
            state (GoalState): The new state to set for the goal.

        Raises:
            ValueError: If the provided state is not a valid GoalState.

        """
        if state not in GoalState:
            raise ValueError('Not a valid state was given')
        if state == self.state:
            return
        self._state = state
        if self._rtmonitor:
            self._send_state_change_event()
        self._report_state()

    def _send_state_change_event(self):
        event = EventMsg(
                type='goal_state',
                data={
                    'goal_name': self.name,
                    'state': self.state.name,
                    'state_int': self.state.value,
                    'duration': self.duration if self.duration > 0 else self.get_current_elapsed(),
                    'ts_start': self._ts_start,
                    'elapsed_time': self.get_current_elapsed(),
                }
        )
        self.log_info(f'Sending goal state change event: {event}')
        self._rtmonitor.send_event(event)

    def _report_state(self):
        self.log_info(f'Goal <{self.__class__.__name__}:{self.name}> entered {self.state.name} state ' +
              f'(maxT={self._max_duration}, minT={self._min_duration})')

    def enter(self, rtmonitor: RTMonitor = None):
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
        self._ts_start = self.get_current_ts()
        if rtmonitor is not None:
            self.set_rtmonitor(rtmonitor)
        self.set_state(GoalState.RUNNING)
        self.on_enter()
        self.run_until_exit()
        return self

    def get_current_ts(self):
        return time.time()

    def get_current_elapsed(self):
        return self.get_current_ts() - self._ts_start

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
        while self._state not in (GoalState.COMPLETED, GoalState.FAILED, GoalState.TERMINATED):
            self.tick()
            elapsed = self.get_current_elapsed()
            if self._max_duration in (None, 0):
                continue
            elif elapsed > self._max_duration:
                self._duration = elapsed
                self.set_state(GoalState.FAILED)
                self.log_info(
                    f'Goal <{self.__class__.__name__}:{self._name}> exited due' + \
                    f' to timeout after {self._max_duration} seconds!')
                break
            time.sleep(1 / self._freq)
        elapsed = self.get_current_elapsed()
        self._duration = elapsed
        if self._min_duration not in (None, 0) and elapsed < self._min_duration:
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

    def log_namespace(self):
        return f"{self.__class__.__name__}:{self.name}"

    def log(self):
        return logger

    def log_info(self, msg):
        self.log().info(f"[{self.log_namespace()}] {msg}")

    def log_warning(self, msg):
        self.log().warning(f"[{self.log_namespace()}] {msg}")

    def log_error(self, msg):
        self.log().error(f"[{self.log_namespace()}] {msg}")

    def log_debug(self, msg):
        self.log().debug(f"[{self.log_namespace()}] {msg}")

    def get_current_ts_ms(self):
        return int(time.time() * 1000)
