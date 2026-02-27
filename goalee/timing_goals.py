"""Timing goal types for runtime verification of temporal properties."""

from __future__ import annotations

import statistics
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable

from goalee.entity import Entity
from goalee.goal import Goal, GoalState


class RateGoal(Goal):
    """Verifies entity publishes at expected interval ± tolerance."""

    def __init__(
        self,
        entity: Entity,
        name: str | None = None,
        interval: float | None = None,
        tolerance: float | None = None,
        jitter: float | None = None,
        window: int = 20,
        event_emitter: Any | None = None,
        max_duration: float | None = None,
        min_duration: float | None = None,
        for_duration: float | None = None,
    ):
        super().__init__(
            [entity],
            event_emitter,
            name=name,
            max_duration=max_duration,
            min_duration=min_duration,
            for_duration=for_duration,
        )
        self.entity = entity
        self._interval = interval  # expected interval in seconds
        self._tolerance = tolerance  # acceptable deviation in seconds
        self._jitter = jitter  # max acceptable jitter (std of intervals)
        self._window = window
        self._timestamps: deque = deque(maxlen=window)
        self._last_state: dict | None = None

    def on_enter(self):
        self.log_debug(
            f"Starting RateGoal <{self.name}>:\n"
            f"Entity: {self.entity.name}\n"
            f"Interval: {self._interval}s\n"
            f"Tolerance: {self._tolerance}s\n"
            f"Window: {self._window}"
        )
        self._last_state = None

    def tick(self):
        current_state = self.entity.attributes.copy()
        if self._last_state is None:
            self._last_state = current_state
            self._timestamps.append(time.time())
            return

        if current_state != self._last_state:
            self._timestamps.append(time.time())
            self._last_state = current_state

        if len(self._timestamps) < 2:
            return

        # Calculate intervals between consecutive timestamps
        intervals = [
            self._timestamps[i + 1] - self._timestamps[i]
            for i in range(len(self._timestamps) - 1)
        ]

        if not intervals:
            return

        avg_interval = statistics.mean(intervals)

        # Check if average interval is within tolerance of expected
        if self._tolerance is not None and self._interval is not None:
            if abs(avg_interval - self._interval) <= self._tolerance:
                # Check jitter if specified
                if self._jitter is not None and len(intervals) > 1:
                    interval_jitter = statistics.stdev(intervals)
                    if interval_jitter <= self._jitter:
                        self.set_state(GoalState.COMPLETED)
                else:
                    self.set_state(GoalState.COMPLETED)


class LatencyGoal(Goal):
    """Measures time between trigger and response events."""

    def __init__(
        self,
        trigger_entities: list[Entity] | None = None,
        response_entities: list[Entity] | None = None,
        name: str | None = None,
        trigger_condition: Callable | None = None,
        response_condition: Callable | None = None,
        max_latency: float | None = None,
        event_emitter: Any | None = None,
        max_duration: float | None = None,
        min_duration: float | None = None,
        for_duration: float | None = None,
    ):
        all_entities = list(set((trigger_entities or []) + (response_entities or [])))
        super().__init__(
            all_entities,
            event_emitter,
            name=name,
            max_duration=max_duration,
            min_duration=min_duration,
            for_duration=for_duration,
        )
        self._trigger_entities = trigger_entities or []
        self._response_entities = response_entities or []
        self._trigger_condition = trigger_condition
        self._response_condition = response_condition
        self._max_latency = max_latency
        self._trigger_ts: float | None = None

    def on_enter(self):
        self.log_debug(
            f"Starting LatencyGoal <{self.name}>:\nMax Latency: {self._max_latency}s"
        )
        self._trigger_ts = None

    def _get_entities_map(self, entities):
        return {e.name: e for e in entities}

    def tick(self):
        try:
            # Check trigger
            if self._trigger_ts is None:
                if self._trigger_condition is not None:
                    e_map = self._get_entities_map(self._trigger_entities)
                    if callable(self._trigger_condition):
                        if self._trigger_condition(e_map):
                            self._trigger_ts = time.time()
                else:
                    # Entity-based trigger: any state change
                    self._trigger_ts = time.time()
                return

            # Check response
            if self._response_condition is not None:
                e_map = self._get_entities_map(self._response_entities)
                if callable(self._response_condition):
                    if self._response_condition(e_map):
                        latency = time.time() - self._trigger_ts
                        if (
                            self._max_latency is not None
                            and latency <= self._max_latency
                        ):
                            self.set_state(GoalState.COMPLETED)
                        else:
                            self.set_state(GoalState.FAILED)
            else:
                # Entity-based response: any state change
                latency = time.time() - self._trigger_ts
                if self._max_latency is not None and latency <= self._max_latency:
                    self.set_state(GoalState.COMPLETED)
                else:
                    self.set_state(GoalState.FAILED)
        except TypeError:
            self.log_debug("Condition evaluation skipped (entity not yet initialized)")


class OrderingGoal(Goal):
    """Verifies goals complete in specified sequence within time window."""

    def __init__(
        self,
        goals: list[str] | None = None,
        name: str | None = None,
        within: float | None = None,
        event_emitter: Any | None = None,
        max_duration: float | None = None,
        min_duration: float | None = None,
        for_duration: float | None = None,
    ):
        super().__init__(
            [],
            event_emitter,
            name=name,
            max_duration=max_duration,
            min_duration=min_duration,
            for_duration=for_duration,
        )
        self._goal_names = goals or []
        self._within = within
        self._completed_order: list[str] = []

    def on_enter(self):
        self.log_debug(
            f"Starting OrderingGoal <{self.name}>:\n"
            f"Sequence: {self._goal_names}\n"
            f"Within: {self._within}s"
        )
        self._completed_order = []

    def tick(self):
        # In a real scenario, this would check goal completion order
        # via the scenario's goal registry. Placeholder for now.
        pass


class DeadlineGoal(Goal):
    """Condition must be met by absolute wall-clock time."""

    def __init__(
        self,
        entities: list[Entity] | None = None,
        name: str | None = None,
        condition: Callable | None = None,
        deadline_time: str | None = None,
        after_time: str | None = None,
        event_emitter: Any | None = None,
        max_duration: float | None = None,
        min_duration: float | None = None,
        for_duration: float | None = None,
    ):
        super().__init__(
            entities,
            event_emitter,
            name=name,
            max_duration=max_duration,
            min_duration=min_duration,
            for_duration=for_duration,
        )
        self._condition = condition
        self._deadline_time = deadline_time
        self._after_time = after_time

    def on_enter(self):
        self.log_debug(
            f"Starting DeadlineGoal <{self.name}>:\n"
            f"Deadline: {self._deadline_time}\n"
            f"After: {self._after_time}"
        )

    def _parse_time(self, time_str: str) -> datetime:
        parts = time_str.split(":")
        now = datetime.now()
        return now.replace(
            hour=int(parts[0]),
            minute=int(parts[1]) if len(parts) > 1 else 0,
            second=int(parts[2]) if len(parts) > 2 else 0,
            microsecond=0,
        )

    def _get_entities_map(self):
        return {e.name: e for e in self._entities}

    def tick(self):
        now = datetime.now()

        # Check if we're past the after time (if specified)
        if self._after_time is not None:
            after_dt = self._parse_time(self._after_time)
            if now < after_dt:
                return

        # Check deadline
        if self._deadline_time is not None:
            deadline_dt = self._parse_time(self._deadline_time)
            if now > deadline_dt:
                self.set_state(GoalState.FAILED)
                return

        # Evaluate condition
        try:
            if self._condition is not None:
                if callable(self._condition):
                    e_map = self._get_entities_map()
                    if self._condition(e_map):
                        self.set_state(GoalState.COMPLETED)
        except TypeError:
            self.log_debug("Condition evaluation skipped (entity not yet initialized)")
