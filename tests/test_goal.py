from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from goalee.entity import Entity
from goalee.goal import Goal, GoalState


class MockGoal(Goal):
    def __init__(self, complete_after_ticks=1, **kwargs):
        super().__init__(**kwargs)
        self._tick_count = 0
        self._complete_after = complete_after_ticks

    def on_enter(self):
        pass

    def tick(self):
        self._tick_count += 1
        if self._tick_count >= self._complete_after:
            self.set_state(GoalState.COMPLETED)


class TestGoalState:
    def test_enum_values(self):
        assert GoalState.IDLE == 0
        assert GoalState.RUNNING == 1
        assert GoalState.COMPLETED == 2
        assert GoalState.FAILED == 3
        assert GoalState.TERMINATED == 4

    def test_enum_names(self):
        assert GoalState.IDLE.name == "IDLE"
        assert GoalState.COMPLETED.name == "COMPLETED"


class TestGoalCreation:
    def test_defaults(self):
        g = MockGoal()
        assert g.state == GoalState.IDLE
        assert g.entities == []
        assert g.name is not None
        assert len(g.name) > 0
        assert g._max_duration is None
        assert g._min_duration is None
        assert g._for_duration is None
        assert g._freq == 10

    def test_explicit_name(self):
        g = MockGoal(name="my_goal")
        assert g.name == "my_goal"

    def test_empty_name_generates_random(self):
        g = MockGoal(name="")
        assert len(g.name) > 0
        assert g.name != ""

    def test_none_name_generates_random(self):
        g = MockGoal(name=None)
        assert len(g.name) > 0

    def test_with_entities(self):
        e = Entity(name="e1", etype="sensor", topic="t", attributes=["a"])
        g = MockGoal(entities=[e])
        assert len(g.entities) == 1
        assert g.entities[0].name == "e1"

    def test_with_durations(self):
        g = MockGoal(max_duration=10.0, min_duration=1.0, for_duration=5.0)
        assert g._max_duration == 10.0
        assert g._min_duration == 1.0
        assert g._for_duration == 5.0

    def test_with_tick_freq(self):
        g = MockGoal(tick_freq=20)
        assert g._freq == 20


class TestGoalSetState:
    def test_valid_states(self):
        g = MockGoal()
        for state in GoalState:
            g._state = GoalState.IDLE  # reset to avoid same-state no-op
            g.set_state(state)
            assert g.state == state

    def test_invalid_state_raises(self):
        g = MockGoal()
        with pytest.raises((ValueError, TypeError)):
            g.set_state(99)

    def test_same_state_noop(self):
        g = MockGoal()
        assert g.state == GoalState.IDLE
        g.set_state(GoalState.IDLE)
        assert g.state == GoalState.IDLE


class TestGoalProperties:
    def test_name(self):
        g = MockGoal(name="test")
        assert g.name == "test"

    def test_state(self):
        g = MockGoal()
        assert g.state == GoalState.IDLE

    def test_status_false_when_idle(self):
        g = MockGoal()
        assert g.status is False

    def test_status_true_when_completed(self):
        g = MockGoal()
        g.set_state(GoalState.RUNNING)
        g.set_state(GoalState.COMPLETED)
        assert g.status is True

    def test_status_false_when_failed(self):
        g = MockGoal()
        g.set_state(GoalState.RUNNING)
        g.set_state(GoalState.FAILED)
        assert g.status is False

    def test_entities(self):
        g = MockGoal()
        assert g.entities == []

    def test_duration(self):
        g = MockGoal()
        assert g.duration == 0.0  # _ts_exit(-1) - _ts_start(-1) = 0


class TestGoalSetTickFreq:
    def test_set_tick_freq(self):
        g = MockGoal()
        g.set_tick_freq(50)
        assert g._freq == 50


class TestGoalSerialize:
    def test_serialize_structure(self):
        e = Entity(name="e1", etype="sensor", topic="t", attributes=["a"])
        g = MockGoal(
            name="test_goal",
            entities=[e],
            max_duration=10.0,
            min_duration=1.0,
            for_duration=5.0,
        )
        result = g.serialize()
        assert result["name"] == "test_goal"
        assert result["type"] == "MockGoal"
        assert result["state"] == "IDLE"
        assert result["max_duration"] == 10.0
        assert result["min_duration"] == 1.0
        assert result["for_duration"] == 5.0
        assert result["entities"] == ["e1"]
        assert "elapsed" in result
        assert "ts_start" in result
        assert "ts_exit" in result


class TestGoalEnter:
    def test_enter_completes(self):
        g = MockGoal(complete_after_ticks=1, name="enter_test")
        result = g.enter()
        assert result is g
        assert g.state == GoalState.COMPLETED
        assert g._ts_start > 0
        assert g._ts_exit > 0

    def test_enter_with_rtmonitor(self):
        mock_rtm = MagicMock()
        g = MockGoal(complete_after_ticks=1, name="rtm_test")
        g.enter(rtmonitor=mock_rtm)
        assert g._rtmonitor is mock_rtm


class TestGoalRunUntilExit:
    def test_completes_on_tick(self):
        g = MockGoal(complete_after_ticks=2, name="run_test")
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.COMPLETED
        assert g._tick_count == 2

    def test_fails_on_max_duration(self):
        class NeverCompleteGoal(Goal):
            def on_enter(self):
                pass

            def tick(self):
                pass

        g = NeverCompleteGoal(name="timeout_test", max_duration=0.001, tick_freq=1000)
        g._ts_start = time.time() - 1.0  # started 1 second ago
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.FAILED

    def test_fails_on_min_duration(self):
        g = MockGoal(complete_after_ticks=1, name="min_dur_test", min_duration=999.0)
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.FAILED

    def test_no_max_duration_continues(self):
        g = MockGoal(complete_after_ticks=3, name="no_max_test", max_duration=None)
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.COMPLETED
        assert g._tick_count == 3

    def test_zero_max_duration_continues(self):
        g = MockGoal(complete_after_ticks=2, name="zero_max_test", max_duration=0)
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.COMPLETED

    def test_terminated_exits_loop(self):
        class TerminateGoal(Goal):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._count = 0

            def on_enter(self):
                pass

            def tick(self):
                self._count += 1
                if self._count >= 2:
                    self.set_state(GoalState.TERMINATED)

        g = TerminateGoal(name="term_test")
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.TERMINATED

    def test_min_duration_none_no_fail(self):
        g = MockGoal(complete_after_ticks=1, name="min_none", min_duration=None)
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.COMPLETED

    def test_min_duration_zero_no_fail(self):
        g = MockGoal(complete_after_ticks=1, name="min_zero", min_duration=0)
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        g.run_until_exit()
        assert g.state == GoalState.COMPLETED


class TestGoalTerminate:
    def test_terminate(self):
        g = MockGoal(name="term")
        g.set_state(GoalState.RUNNING)
        g.terminate()
        assert g.state == GoalState.TERMINATED


class TestGoalReset:
    def test_reset(self):
        g = MockGoal(name="reset_test")
        g.set_state(GoalState.RUNNING)
        g._ts_start = 100.0
        g._ts_hold = 50.0
        g._ts_exit = 200.0
        g._duration = 100.0
        g.reset()
        assert g.state == GoalState.IDLE
        assert g._ts_start == -1.0
        assert g._ts_hold == -1.0
        assert g._ts_exit == -1.0
        assert g._duration == -1.0


class TestGoalLogging:
    def test_log_namespace(self):
        g = MockGoal(name="mygoal")
        assert g.log_namespace() == "MockGoal:mygoal"

    def test_log_info(self):
        g = MockGoal(name="logtest")
        g.log_info("test message")

    def test_log_warning(self):
        g = MockGoal(name="logtest")
        g.log_warning("test warning")

    def test_log_error(self):
        g = MockGoal(name="logtest")
        g.log_error("test error")

    def test_log_debug(self):
        g = MockGoal(name="logtest")
        g.log_debug("test debug")

    def test_log_returns_logger(self):
        g = MockGoal(name="logtest")
        assert g.log() is not None


class TestGoalTimestamps:
    def test_get_current_ts(self):
        g = MockGoal(name="ts_test")
        ts = g.get_current_ts()
        assert isinstance(ts, float)
        assert ts > 0

    def test_get_current_ts_ms(self):
        g = MockGoal(name="ts_ms_test")
        ts_ms = g.get_current_ts_ms()
        assert isinstance(ts_ms, int)
        assert ts_ms > 0

    def test_get_current_elapsed(self):
        g = MockGoal(name="elapsed_test")
        g._ts_start = time.time() - 1.0
        elapsed = g.get_current_elapsed()
        assert elapsed >= 0.9


class TestGoalAbstractMethods:
    def test_on_enter_raises(self):
        g = Goal.__new__(Goal)
        with pytest.raises(NotImplementedError):
            g.on_enter()

    def test_tick_raises(self):
        g = Goal.__new__(Goal)
        with pytest.raises(NotImplementedError):
            g.tick()


class TestGoalGenRandomName:
    def test_generates_unique_names(self):
        g = MockGoal()
        name1 = g._gen_random_name()
        name2 = g._gen_random_name()
        assert name1 != name2
        assert isinstance(name1, str)
        assert len(name1) > 0
        assert "-" not in name1


class TestGoalStateChangeEvent:
    def test_send_state_change_event_with_rtmonitor(self):
        mock_rtm = MagicMock()
        g = MockGoal(name="event_test")
        g._rtmonitor = mock_rtm
        g._ts_start = time.time()
        g.set_state(GoalState.RUNNING)
        assert mock_rtm.send_event.called

    def test_no_event_without_rtmonitor(self):
        g = MockGoal(name="no_rtm")
        g.set_state(GoalState.RUNNING)


class TestGoalReportState:
    def test_report_state_no_crash(self):
        g = MockGoal(name="report_test")
        g._report_state()


class TestGoalOnExit:
    def test_on_exit_sets_ts_exit(self):
        g = MockGoal(name="exit_test")
        g.on_exit()
        assert g._ts_exit > 0

    def test_on_reset_default(self):
        g = MockGoal(name="reset_default")
        g.on_reset()


class TestGoalSetRtmonitor:
    def test_set_rtmonitor(self):
        g = MockGoal(name="rtm_set")
        mock_rtm = MagicMock()
        g.set_rtmonitor(mock_rtm)
        assert g._rtmonitor is mock_rtm


class TestGoalSendStateChangeEventDuration:
    def test_positive_duration(self):
        mock_rtm = MagicMock()
        g = MockGoal(name="dur_pos")
        g._rtmonitor = mock_rtm
        g._ts_start = 100.0
        g._ts_exit = 110.0
        g._state = GoalState.RUNNING
        g.set_state(GoalState.COMPLETED)
        call_args = mock_rtm.send_event.call_args
        event = call_args[0][0]
        assert event.data["duration"] == 10.0

    def test_negative_duration_uses_elapsed(self):
        mock_rtm = MagicMock()
        g = MockGoal(name="dur_neg")
        g._rtmonitor = mock_rtm
        g._ts_start = time.time()
        g._ts_exit = -1.0
        g._state = GoalState.IDLE
        g.set_state(GoalState.RUNNING)
        call_args = mock_rtm.send_event.call_args
        event = call_args[0][0]
        assert event.data["duration"] >= 0
