from __future__ import annotations

from unittest.mock import patch

import pytest

from goalee.complex_goal import ComplexGoal, ComplexGoalAlgorithm
from goalee.goal import Goal, GoalState


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


def test_default_algorithm():
    cg = ComplexGoal(name="cg")
    assert cg._algorithm == ComplexGoalAlgorithm.ALL_ACCOMPLISHED
    assert cg._goals == []
    assert cg._x_accomplished is None


def test_explicit_algorithm_and_accomplished():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED,
        accomplished=2,
    )
    assert cg._algorithm == ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED
    assert cg._x_accomplished == 2


def test_goals_property():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    cg._goals.append(g1)
    assert cg.goals == [g1]


# --- add_goal ---


def test_add_goal_appends():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    cg.add_goal(g1)
    cg.add_goal(g2)
    assert cg.goals == [g1, g2]


def test_add_goal_propagates_max_duration_when_child_none():
    cg = ComplexGoal(name="cg", max_duration=5.0)
    g = MockGoal(name="g1", max_duration=None)
    cg.add_goal(g)
    assert g._max_duration == 5.0


def test_add_goal_propagates_max_duration_when_child_larger():
    cg = ComplexGoal(name="cg", max_duration=5.0)
    g = MockGoal(name="g1", max_duration=10.0)
    cg.add_goal(g)
    assert g._max_duration == 5.0


def test_add_goal_keeps_child_max_duration_when_smaller():
    cg = ComplexGoal(name="cg", max_duration=10.0)
    g = MockGoal(name="g1", max_duration=3.0)
    cg.add_goal(g)
    assert g._max_duration == 3.0


def test_add_goal_no_propagation_when_parent_max_none():
    cg = ComplexGoal(name="cg", max_duration=None)
    g = MockGoal(name="g1", max_duration=5.0)
    cg.add_goal(g)
    assert g._max_duration == 5.0


def test_add_goal_propagates_min_duration_when_child_none():
    cg = ComplexGoal(name="cg", min_duration=2.0)
    g = MockGoal(name="g1", min_duration=None)
    cg.add_goal(g)
    assert g._min_duration == 2.0


def test_add_goal_propagates_min_duration_when_child_smaller():
    cg = ComplexGoal(name="cg", min_duration=5.0)
    g = MockGoal(name="g1", min_duration=2.0)
    cg.add_goal(g)
    assert g._min_duration == 5.0


def test_add_goal_keeps_child_min_duration_when_larger():
    cg = ComplexGoal(name="cg", min_duration=2.0)
    g = MockGoal(name="g1", min_duration=10.0)
    cg.add_goal(g)
    assert g._min_duration == 10.0


def test_add_goal_no_propagation_when_parent_min_none():
    cg = ComplexGoal(name="cg", min_duration=None)
    g = MockGoal(name="g1", min_duration=3.0)
    cg.add_goal(g)
    assert g._min_duration == 3.0


# --- set_state_cascaded ---


def test_set_state_cascaded():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    cg.add_goal(g1)
    cg.add_goal(g2)
    cg.set_state_cascaded(GoalState.TERMINATED)
    assert g1.state == GoalState.TERMINATED
    assert g2.state == GoalState.TERMINATED
    assert cg.state == GoalState.TERMINATED


# --- set_tick_freq ---


def test_set_tick_freq_propagates():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    cg.add_goal(g1)
    cg.add_goal(g2)
    cg.set_tick_freq(50)
    assert g1._freq == 50
    assert g2._freq == 50


# --- serialize ---


def test_serialize():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED)
    g1 = MockGoal(name="g1")
    cg.add_goal(g1)
    data = cg.serialize()
    assert data["algorithm"] == "NONE_ACCOMPLISHED"
    assert data["name"] == "cg"
    assert len(data["goals"]) == 1
    assert data["goals"][0]["name"] == "g1"


# --- reset ---


def test_reset():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1", complete_on_enter=True)
    g2 = MockGoal(name="g2", complete_on_enter=True)
    cg.add_goal(g1)
    cg.add_goal(g2)
    cg.enter()
    assert cg.state == GoalState.COMPLETED
    cg.reset()
    assert cg.state == GoalState.IDLE
    assert g1.state == GoalState.IDLE
    assert g2.state == GoalState.IDLE
    assert cg._ts_start == -1.0
    assert cg._ts_exit == -1.0
    assert cg._duration == -1.0


# --- ALL_ACCOMPLISHED ---


def test_all_accomplished_all_complete():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(MockGoal(complete_on_enter=True, name="g2"))
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_all_accomplished_one_fails():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


def test_all_accomplished_all_fail():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g1", max_duration=0.01
        )
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- NONE_ACCOMPLISHED ---


def test_none_accomplished_all_fail():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED)
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g1", max_duration=0.01
        )
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_none_accomplished_one_completes():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED)
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- AT_LEAST_ONE_ACCOMPLISHED ---


def test_at_least_one_accomplished_one_completes():
    cg = ComplexGoal(
        name="cg", algorithm=ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISHED
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_at_least_one_accomplished_none_complete():
    cg = ComplexGoal(
        name="cg", algorithm=ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISHED
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g1", max_duration=0.01
        )
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- EXACTLY_X_ACCOMPLISHED ---


def test_exactly_x_accomplished_match():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED,
        accomplished=1,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_exactly_x_accomplished_no_match():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED,
        accomplished=2,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- ALL_ACCOMPLISHED_ORDERED (sequential) ---


def test_all_accomplished_ordered_all_complete():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED)
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(MockGoal(complete_on_enter=True, name="g2"))
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_all_accomplished_ordered_one_fails():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED)
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- EXACTLY_X_ACCOMPLISHED_ORDERED (sequential) ---


def test_exactly_x_ordered_match():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED,
        accomplished=1,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.COMPLETED


def test_exactly_x_ordered_no_match():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED_ORDERED,
        accomplished=3,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- run_seq max_duration break ---


def test_run_seq_max_duration_exceeded():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED,
        max_duration=0.001,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.add_goal(MockGoal(complete_on_enter=True, name="g2"))
    cg.add_goal(MockGoal(complete_on_enter=True, name="g3"))
    with patch.object(cg, "get_current_elapsed", return_value=1.0):
        cg.enter()
    assert cg.state == GoalState.FAILED


# --- run_concurrent timeout ---


def test_run_concurrent_timeout():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED,
        max_duration=0.001,
    )

    class SlowGoal(Goal):
        def on_enter(self):
            pass

        def tick(self):
            import time

            time.sleep(0.1)

    cg.add_goal(SlowGoal(name="slow1", max_duration=10.0))
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- run_concurrent exception in goal ---


def test_run_concurrent_goal_exception():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)

    class ErrorGoal(Goal):
        def on_enter(self):
            pass

        def tick(self):
            raise RuntimeError("boom")

    cg.add_goal(ErrorGoal(name="err", max_duration=0.01))
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- terminate ---


def test_terminate():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.RUNNING)
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.COMPLETED)
    cg.add_goal(g1)
    cg.add_goal(g2)
    cg.terminate()
    assert g1.state == GoalState.TERMINATED
    assert g2.state == GoalState.COMPLETED
    assert cg.state == GoalState.TERMINATED


# --- terminate_all_goals ---


def test_terminate_all_goals_skips_finished():
    cg = ComplexGoal(name="cg")
    g_completed = MockGoal(name="gc")
    g_completed.set_state(GoalState.COMPLETED)
    g_failed = MockGoal(name="gf")
    g_failed.set_state(GoalState.FAILED)
    g_terminated = MockGoal(name="gt")
    g_terminated.set_state(GoalState.TERMINATED)
    g_running = MockGoal(name="gr")
    g_running.set_state(GoalState.RUNNING)
    cg.add_goal(g_completed)
    cg.add_goal(g_failed)
    cg.add_goal(g_terminated)
    cg.add_goal(g_running)
    cg.terminate_all_goals()
    assert g_completed.state == GoalState.COMPLETED
    assert g_failed.state == GoalState.FAILED
    assert g_terminated.state == GoalState.TERMINATED
    assert g_running.state == GoalState.TERMINATED


# --- _get_results_list ---


def test_get_results_list():
    cg = ComplexGoal(name="cg")
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.FAILED)
    g3 = MockGoal(name="g3")
    g3.set_state(GoalState.COMPLETED)
    cg.add_goal(g1)
    cg.add_goal(g2)
    cg.add_goal(g3)
    assert cg._get_results_list() == [1, 0, 1]


def test_get_results_list_empty():
    cg = ComplexGoal(name="cg")
    assert cg._get_results_list() == []


# --- enter with min_duration failure ---


def test_enter_min_duration_not_met():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED,
        min_duration=1000.0,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- enter with max_duration exceeded for non-NONE algorithms ---


def test_enter_max_duration_exceeded_all_accomplished():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED,
        max_duration=0.001,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    with patch.object(cg, "get_current_elapsed", return_value=1.0):
        cg.enter()
    assert cg.state == GoalState.FAILED


# --- enter when state is already FAILED (no further state change) ---


def test_enter_already_failed_no_change():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g1", max_duration=0.01
        )
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g2", max_duration=0.01
        )
    )
    cg.enter()
    assert cg.state == GoalState.FAILED


# --- enter returns self ---


def test_enter_returns_self():
    cg = ComplexGoal(name="cg")
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    result = cg.enter()
    assert result is cg


# --- NONE_ACCOMPLISHED with max_duration exceeded does NOT fail from enter ---


def test_none_accomplished_max_duration_not_failed_by_enter():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED,
        max_duration=0.001,
    )
    cg.add_goal(
        MockGoal(
            complete_on_enter=False, fail_on_enter=True, name="g1", max_duration=0.001
        )
    )
    cg.enter()
    assert cg.state == GoalState.COMPLETED


# --- EXACTLY_X with max_duration exceeded does NOT fail from enter ---


def test_exactly_x_max_duration_not_failed_by_enter():
    cg = ComplexGoal(
        name="cg",
        algorithm=ComplexGoalAlgorithm.EXACTLY_X_ACCOMPLISHED,
        accomplished=1,
        max_duration=0.001,
    )
    cg.add_goal(MockGoal(complete_on_enter=True, name="g1"))
    cg.enter()
    assert cg.state == GoalState.COMPLETED


# --- No goals (ThreadPoolExecutor(0) raises ValueError) ---


def test_no_goals_raises_value_error():
    cg = ComplexGoal(name="cg", algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED)
    with pytest.raises(ValueError):
        cg.enter()
