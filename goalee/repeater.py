from typing import Any, Optional

from commlib.node import Node
from goalee.goal import Goal, GoalState
from goalee.rtmonitor import RTMonitor


class GoalRepeater(Goal):

    def __init__(self,
                 goal: Goal,
                 times: int,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
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
        self._goal = goal

        self._repeat_times = times
        self._times = 0

        if (self._goal._max_duration is None or self._goal._max_duration > self._max_duration) and self._max_duration is not None:
            self._goal._max_duration = self._max_duration

    def set_tick_freq(self, freq: int):
        self._goal.set_tick_freq(freq)

    def on_enter(self):
        self.log_info(f'Starting Goal-Repeater <{self._name}>:\n'
                      f"Parameters:\n"
                      f"  Goal: {self._goal.__class__.__name__}:{self._goal.name}\n"
                      f"  Times: {self._repeat_times}\n"
                      f"  Max Duration: {self._max_duration}\n"
                      f"  Min Duration: {self._min_duration}")

    def enter(self, rtmonitor: RTMonitor = None):
        self._ts_start = self.get_current_ts()
        self.on_enter()
        _states = []
        _durations = []
        while self._times < self._repeat_times and self._state == GoalState.RUNNING:
            self._times += 1
            self._goal.enter()
            _states.append(self._goal.state)
            _durations.append(self._goal.duration)
            if self._max_duration not in (None, 0) and self.get_current_elapsed() > self._max_duration:
                break
            self._goal.reset()
        elapsed = self.get_current_elapsed()
        if self._max_duration not in (None, 0) and elapsed > self._max_duration:
            self.set_state(GoalState.FAILED)
        elif self._min_duration not in (None, 0) and elapsed < self._min_duration:
            self.set_state(GoalState.FAILED)
        elif self._state == GoalState.RUNNING:
            self.set_state(GoalState.COMPLETED if all([s == GoalState.COMPLETED for s in _states]) else GoalState.FAILED)
        else:  # Terminated / Failed
            pass
        self.on_exit()
        return self
