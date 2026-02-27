from __future__ import annotations

from unittest.mock import patch

from goalee.goal import Goal, GoalState
from goalee.repeater import GoalRepeater


class MockGoal(Goal):
    def __init__(self, complete_on_enter=True, fail_on_enter=False, **kwargs):
        super().__init__(**kwargs)
        self._complete_on_enter = complete_on_enter
        self._fail_on_enter = fail_on_enter

    def on_enter(self):
        pass

    def tick(self):
        if self._complete_on_enter:
            self.set_state(GoalState.COMPLETED)
        elif self._fail_on_enter:
            self.set_state(GoalState.FAILED)


# --- Construction ---


def test_creation_basic():
    inner = MockGoal(name="inner")
    rep = GoalRepeater(inner, times=3, name="rep")
    assert rep._goal is inner
    assert rep._repeat_times == 3
    assert rep._times == 0
    assert rep.name == "rep"


def test_creation_propagates_max_duration_when_child_none():
    inner = MockGoal(name="inner", max_duration=None)
    GoalRepeater(inner, times=3, name="rep", max_duration=5.0)
    assert inner._max_duration == 5.0


def test_creation_propagates_max_duration_when_child_larger():
    inner = MockGoal(name="inner", max_duration=10.0)
    GoalRepeater(inner, times=3, name="rep", max_duration=5.0)
    assert inner._max_duration == 5.0


def test_creation_keeps_child_max_duration_when_smaller():
    inner = MockGoal(name="inner", max_duration=2.0)
    GoalRepeater(inner, times=3, name="rep", max_duration=5.0)
    assert inner._max_duration == 2.0


def test_creation_no_propagation_when_parent_max_none():
    inner = MockGoal(name="inner", max_duration=None)
    GoalRepeater(inner, times=3, name="rep", max_duration=None)
    assert inner._max_duration is None


# --- set_tick_freq ---


def test_set_tick_freq_propagates():
    inner = MockGoal(name="inner")
    rep = GoalRepeater(inner, times=2, name="rep")
    rep.set_tick_freq(100)
    assert inner._freq == 100


# --- serialize ---


def test_serialize():
    inner = MockGoal(name="inner")
    rep = GoalRepeater(inner, times=5, name="rep")
    data = rep.serialize()
    assert data["times"] == 5
    assert data["name"] == "rep"
    assert len(data["goals"]) == 1
    assert data["goals"][0]["name"] == "inner"


# --- on_enter (no crash) ---


def test_on_enter_no_crash():
    inner = MockGoal(name="inner")
    rep = GoalRepeater(inner, times=1, name="rep")
    rep.on_enter()


# --- enter: all iterations complete ---


def test_repeat_all_complete():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=3, name="rep")
    rep.enter()
    assert rep.state == GoalState.COMPLETED
    assert rep._times == 3


def test_repeat_single_iteration():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=1, name="rep")
    rep.enter()
    assert rep.state == GoalState.COMPLETED
    assert rep._times == 1


# --- enter: inner goal fails ---


def test_repeat_inner_fails():
    inner = MockGoal(
        complete_on_enter=False, fail_on_enter=True, name="inner", max_duration=0.01
    )
    rep = GoalRepeater(inner, times=3, name="rep", max_duration=1.0)
    rep.enter()
    assert rep.state == GoalState.FAILED


# --- enter: max_duration exceeded ---


def test_repeat_max_duration_exceeded():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=100, name="rep", max_duration=0.001)
    with patch.object(rep, "get_current_elapsed", return_value=1.0):
        rep.enter()
    assert rep.state == GoalState.FAILED


# --- enter: min_duration not met ---


def test_repeat_min_duration_not_met():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=1, name="rep", min_duration=1000.0)
    rep.enter()
    assert rep.state == GoalState.FAILED


# --- enter: terminated mid-loop ---


def test_repeat_terminated_mid_loop():
    call_count = 0

    class TerminatingGoal(Goal):
        def on_enter(self):
            pass

        def tick(self):
            nonlocal call_count
            call_count += 1
            self.set_state(GoalState.COMPLETED)

    inner = TerminatingGoal(name="inner")
    rep = GoalRepeater(inner, times=5, name="rep")

    original_enter = inner.enter

    def enter_and_terminate(*args, **kwargs):
        result = original_enter(*args, **kwargs)
        if rep._times >= 2:
            rep.set_state(GoalState.TERMINATED)
        return result

    with patch.object(inner, "enter", side_effect=enter_and_terminate):
        rep.enter()

    assert rep.state == GoalState.TERMINATED


# --- enter: returns self ---


def test_enter_returns_self():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=1, name="rep")
    result = rep.enter()
    assert result is rep


# --- enter: goal resets between iterations ---


def test_goal_resets_between_iterations():
    reset_count = 0

    class TrackingGoal(MockGoal):
        def reset(self):
            nonlocal reset_count
            reset_count += 1
            super().reset()

    inner = TrackingGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=3, name="rep")
    rep.enter()
    assert reset_count == 3


# --- enter: state is FAILED when inner fails mid-loop ---


def test_repeat_inner_fails_on_second_iteration():
    iteration = 0

    class FailOnSecond(Goal):
        def on_enter(self):
            pass

        def tick(self):
            nonlocal iteration
            iteration += 1
            if iteration >= 2:
                self.set_state(GoalState.FAILED)
            else:
                self.set_state(GoalState.COMPLETED)

    inner = FailOnSecond(name="inner", max_duration=0.1)
    rep = GoalRepeater(inner, times=3, name="rep", max_duration=1.0)
    rep.enter()
    assert rep.state == GoalState.FAILED


# --- enter: state breaks when already FAILED/COMPLETED ---


def test_repeat_breaks_when_state_not_running():
    inner = MockGoal(complete_on_enter=True, name="inner")
    rep = GoalRepeater(inner, times=5, name="rep")

    original_enter = inner.enter

    def enter_and_fail(*args, **kwargs):
        result = original_enter(*args, **kwargs)
        if rep._times >= 2:
            rep.set_state(GoalState.FAILED)
        return result

    with patch.object(inner, "enter", side_effect=enter_and_fail):
        rep.enter()

    assert rep.state == GoalState.FAILED
    assert rep._times < 5
