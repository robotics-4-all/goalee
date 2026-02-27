from __future__ import annotations

from concurrent.futures import Future
from unittest.mock import MagicMock, patch

from goalee.complex_goal import ComplexGoal
from goalee.goal import Goal, GoalState
from goalee.repeater import GoalRepeater
from goalee.scenario import Scenario


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


def test_creation_with_name():
    s = Scenario(name="test_scenario", broker=None)
    assert s.name == "test_scenario"


def test_creation_empty_name_auto_generates():
    s = Scenario(name="", broker=None)
    assert len(s.name) > 0
    assert s.name != ""


def test_creation_none_name_auto_generates():
    s = Scenario(name=None, broker=None)
    assert len(s.name) > 0


def test_creation_with_goals():
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    assert len(s._goals) == 2


def test_creation_with_anti_goals():
    ag = MockGoal(name="ag1")
    s = Scenario(name="s", broker=None, anti_goals=[ag])
    assert len(s._anti_goals) == 1


def test_creation_with_fatal_goals():
    fg = MockGoal(name="fg1")
    s = Scenario(name="s", broker=None, fatal_goals=[fg])
    assert len(s._fatal_goals) == 1


def test_creation_without_broker_node_is_none():
    s = Scenario(name="s", broker=None)
    assert s._node is None


def test_creation_defaults():
    s = Scenario(name="s", broker=None)
    assert s._goals == []
    assert s._anti_goals == []
    assert s._fatal_goals == []
    assert s._rtmonitor is None


# --- name property ---


def test_name_property():
    s = Scenario(name="my_scenario", broker=None)
    assert s.name == "my_scenario"


# --- add_goal ---


def test_add_goal():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="g1")
    s.add_goal(g)
    assert g in s._goals
    assert len(s._goals) == 1


def test_add_goal_with_weight():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="g1")
    s.add_goal(g, weight=0.5)
    assert s._goal_weights is not None
    assert 0.5 in s._goal_weights


def test_add_goal_initializes_weights_when_none():
    s = Scenario(name="s", broker=None)
    g1 = MockGoal(name="g1")
    s.add_goal(g1)
    assert s._goal_weights is not None
    assert len(s._goal_weights) == 1


# --- _update_goal_weights ---


def test_update_goal_weights_equal():
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    assert len(s._goal_weights) == 2
    assert abs(s._goal_weights[0] - 0.5) < 1e-9
    assert abs(s._goal_weights[1] - 0.5) < 1e-9


def test_update_goal_weights_mismatch_reinitializes():
    g1 = MockGoal(name="g1")
    g2 = MockGoal(name="g2")
    s = Scenario(name="s", broker=None, goals=[g1, g2], goal_weights=[1.0])
    assert len(s._goal_weights) == 2


def test_update_antigoal_weights_equal():
    ag1 = MockGoal(name="ag1")
    ag2 = MockGoal(name="ag2")
    s = Scenario(name="s", broker=None, anti_goals=[ag1, ag2])
    assert len(s._antigoal_weights) == 2
    assert abs(s._antigoal_weights[0] - 0.5) < 1e-9


def test_update_antigoal_weights_mismatch_reinitializes():
    ag1 = MockGoal(name="ag1")
    ag2 = MockGoal(name="ag2")
    s = Scenario(name="s", broker=None, anti_goals=[ag1, ag2], antigoal_weights=[1.0])
    assert len(s._antigoal_weights) == 2


def test_update_goal_weights_no_goals():
    s = Scenario(name="s", broker=None)
    assert s._goal_weights is None


def test_update_antigoal_weights_no_antigoals():
    s = Scenario(name="s", broker=None)
    assert s._antigoal_weights is None


# --- build_entity_list ---


def test_build_entity_list():
    e1 = MagicMock()
    e1.name = "e1"
    e2 = MagicMock()
    e2.name = "e2"
    g1 = MockGoal(name="g1")
    g1._entities = [e1]
    g2 = MockGoal(name="g2")
    g2._entities = [e2]
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    s.build_entity_list()
    assert e1 in s._entities
    assert e2 in s._entities


def test_build_entity_list_no_duplicates():
    e1 = MagicMock()
    e1.name = "e1"
    g1 = MockGoal(name="g1")
    g1._entities = [e1]
    g2 = MockGoal(name="g2")
    g2._entities = [e1]
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    s.build_entity_list()
    assert len(s._entities) == 1


# --- calc_score ---


def test_calc_score_all_completed():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g1._ts_start = 0
    g1._ts_exit = 1
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.COMPLETED)
    g2._ts_start = 0
    g2._ts_exit = 1
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    assert abs(s.calc_score() - 1.0) < 1e-9


def test_calc_score_all_failed():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.FAILED)
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.FAILED)
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    assert abs(s.calc_score() - 0.0) < 1e-9


def test_calc_score_no_goals():
    s = Scenario(name="s", broker=None)
    assert s.calc_score() == 0


def test_calc_score_with_antigoals():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g1._ts_start = 0
    g1._ts_exit = 1
    ag1 = MockGoal(name="ag1")
    ag1.set_state(GoalState.COMPLETED)
    ag1._ts_start = 0
    ag1._ts_exit = 1
    s = Scenario(name="s", broker=None, goals=[g1], anti_goals=[ag1])
    assert abs(s.calc_score() - 0.0) < 1e-9


def test_calc_score_mixed():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g1._ts_start = 0
    g1._ts_exit = 1
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.FAILED)
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    assert abs(s.calc_score() - 0.5) < 1e-9


# --- make_result_list ---


def test_make_result_list():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g1._ts_start = 0
    g1._ts_exit = 1
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.FAILED)
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    result = s.make_result_list()
    assert result == [("g1", True), ("g2", False)]


def test_make_result_list_empty():
    s = Scenario(name="s", broker=None)
    assert s.make_result_list() == []


# --- get_current_ts ---


def test_get_current_ts_returns_int():
    ts = Scenario.get_current_ts()
    assert isinstance(ts, int)


def test_get_current_ts_positive():
    ts = Scenario.get_current_ts()
    assert ts > 0


# --- Logging (no crash) ---


def test_log_info_no_crash():
    s = Scenario(name="s", broker=None)
    s.log_info("test message")


def test_log_warning_no_crash():
    s = Scenario(name="s", broker=None)
    s.log_warning("test warning")


def test_log_error_no_crash():
    s = Scenario(name="s", broker=None)
    s.log_error("test error")


def test_log_debug_no_crash():
    s = Scenario(name="s", broker=None)
    s.log_debug("test debug")


def test_log_namespace():
    s = Scenario(name="my_s", broker=None)
    assert s.log_namespace() == "Scenario:my_s"


# --- print_stats / print_results (no crash) ---


def test_print_stats_no_crash():
    s = Scenario(name="s", broker=None)
    s.print_stats()


def test_print_results_no_crash():
    s = Scenario(name="s", broker=None)
    s.print_results()


def test_print_results_with_goals():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.COMPLETED)
    g1._ts_start = 0
    g1._ts_exit = 1
    s = Scenario(name="s", broker=None, goals=[g1])
    s.print_results()


# --- stop_thread_executor ---


def test_stop_thread_executor_no_crash():
    s = Scenario(name="s", broker=None)
    s.stop_thread_executor()


def test_stop_thread_executor_suppresses_exception():
    s = Scenario(name="s", broker=None)
    s._thread_executor = MagicMock()
    s._thread_executor.shutdown.side_effect = RuntimeError("boom")
    s.stop_thread_executor()


# --- terminate_goals ---


def test_terminate_goals():
    g1 = MockGoal(name="g1")
    g1.set_state(GoalState.RUNNING)
    g2 = MockGoal(name="g2")
    g2.set_state(GoalState.COMPLETED)
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    s.terminate_goals()
    assert g1.state == GoalState.TERMINATED
    assert g2.state == GoalState.COMPLETED


def test_terminate_antigoals():
    ag1 = MockGoal(name="ag1")
    ag1.set_state(GoalState.RUNNING)
    ag2 = MockGoal(name="ag2")
    ag2.set_state(GoalState.FAILED)
    s = Scenario(name="s", broker=None, anti_goals=[ag1, ag2])
    s.terminate_antigoals()
    assert ag1.state == GoalState.TERMINATED
    assert ag2.state == GoalState.FAILED


def test_terminate_fatal_goals():
    fg1 = MockGoal(name="fg1")
    fg1.set_state(GoalState.RUNNING)
    fg2 = MockGoal(name="fg2")
    fg2.set_state(GoalState.TERMINATED)
    s = Scenario(name="s", broker=None, fatal_goals=[fg1, fg2])
    s.terminate_fatal_goals()
    assert fg1.state == GoalState.TERMINATED
    assert fg2.state == GoalState.TERMINATED


def test_terminate_all_goals():
    g = MockGoal(name="g")
    g.set_state(GoalState.RUNNING)
    ag = MockGoal(name="ag")
    ag.set_state(GoalState.RUNNING)
    fg = MockGoal(name="fg")
    fg.set_state(GoalState.RUNNING)
    s = Scenario(name="s", broker=None, goals=[g], anti_goals=[ag], fatal_goals=[fg])
    s.terminate_all_goals()
    assert g.state == GoalState.TERMINATED
    assert ag.state == GoalState.TERMINATED
    assert fg.state == GoalState.TERMINATED


# --- RTMonitor ---


def test_init_rtmonitor_without_node_logs_warning():
    s = Scenario(name="s", broker=None)
    s.init_rtmonitor("etopic", "ltopic")
    assert s._rtmonitor is None


def test_send_scenario_started_without_rtmonitor():
    s = Scenario(name="s", broker=None)
    s.send_scenario_started("sequential")


def test_send_scenario_update_without_rtmonitor():
    s = Scenario(name="s", broker=None)
    s.send_scenario_update("concurrent")


def test_send_scenario_finished_without_rtmonitor():
    s = Scenario(name="s", broker=None)
    s.send_scenario_finished("sequential")


# --- gen_random_name ---


def test_gen_random_name():
    s = Scenario(name="s", broker=None)
    name = s.gen_random_name()
    assert isinstance(name, str)
    assert len(name) > 0
    assert "-" not in name


# --- start_entities ---


def test_start_entities_regular_goal():
    e1 = MagicMock()
    g = MockGoal(name="g1")
    g._entities = [e1]
    s = Scenario(name="s", broker=None)
    s.start_entities([g])
    e1.start.assert_called_once()


def test_start_entities_complex_goal():
    e1 = MagicMock()
    inner_g = MockGoal(name="inner")
    inner_g._entities = [e1]
    cg = ComplexGoal(name="cg")
    cg.add_goal(inner_g)
    s = Scenario(name="s", broker=None)
    s.start_entities([cg])
    e1.start.assert_called_once()


def test_start_entities_repeater_goal():
    e1 = MagicMock()
    inner_g = MockGoal(name="inner")
    inner_g._entities = [e1]
    rep = GoalRepeater(inner_g, times=3, name="rep")
    s = Scenario(name="s", broker=None)
    s.start_entities([rep])
    e1.start.assert_called_once()


def test_start_entities_moving_area_goal():
    from goalee.area_goals import MovingAreaGoal

    motion_entity = MagicMock()
    motion_entity.start = MagicMock()
    entity = MagicMock()
    entity.start = MagicMock()

    mag = MagicMock(spec=MovingAreaGoal)
    mag.__class__ = MovingAreaGoal
    mag.motion_entity = motion_entity
    mag.entities = [entity]

    s = Scenario(name="s", broker=None)
    s.start_entities([mag])
    motion_entity.start.assert_called_once()
    entity.start.assert_called_once()


def test_start_entities_moving_area_goal_no_motion_entity():
    from goalee.area_goals import MovingAreaGoal

    entity = MagicMock()
    entity.start = MagicMock()

    mag = MagicMock(spec=MovingAreaGoal)
    mag.__class__ = MovingAreaGoal
    mag.motion_entity = None
    mag.entities = [entity]

    s = Scenario(name="s", broker=None)
    s.start_entities([mag])
    entity.start.assert_called_once()


# --- Callbacks ---


def test_on_goal_callback():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="g1")
    g.set_state(GoalState.COMPLETED)
    g._ts_start = 0
    g._ts_exit = 1
    future = Future()
    future.set_result(g)
    s.on_goal(future)


def test_on_antigoal_callback():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="ag1")
    g.set_state(GoalState.COMPLETED)
    g._ts_start = 0
    g._ts_exit = 1
    future = Future()
    future.set_result(g)
    s.on_antigoal(future)


def test_on_fatal_callback_completed():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="fg1")
    g.set_state(GoalState.COMPLETED)
    g._ts_start = 0
    g._ts_exit = 1

    running_g = MockGoal(name="rg")
    running_g.set_state(GoalState.RUNNING)
    s._goals = [running_g]

    future = Future()
    future.set_result(g)
    s.on_fatal(future)
    assert running_g.state == GoalState.TERMINATED


def test_on_fatal_callback_not_completed():
    s = Scenario(name="s", broker=None)
    g = MockGoal(name="fg1")
    g.set_state(GoalState.FAILED)

    running_g = MockGoal(name="rg")
    running_g.set_state(GoalState.RUNNING)
    s._goals = [running_g]

    future = Future()
    future.set_result(g)
    s.on_fatal(future)
    assert running_g.state == GoalState.RUNNING


# --- goal_tick_freq_hz propagation ---


def test_tick_freq_propagated_to_goals():
    g = MockGoal(name="g1")
    ag = MockGoal(name="ag1")
    fg = MockGoal(name="fg1")
    Scenario(
        name="s",
        broker=None,
        goals=[g],
        anti_goals=[ag],
        fatal_goals=[fg],
        goal_tick_freq_hz=42,
    )
    assert g._freq == 42
    assert ag._freq == 42
    assert fg._freq == 42


# --- log method ---


def test_log_returns_logger():
    s = Scenario(name="s", broker=None)
    assert s.log() is not None


# --- start_goals ---


def test_start_goals():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    g2 = MockGoal(complete_on_enter=True, name="g2")
    s = Scenario(name="s", broker=None, goals=[g1, g2])
    futures = s.start_goals()
    assert len(futures) == 2
    for f in futures:
        f.result()
    s.stop_thread_executor()


# --- start_goals_and_wait ---


def test_start_goals_and_wait():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    s = Scenario(name="s", broker=None, goals=[g1])
    futures = s.start_goals_and_wait()
    assert len(futures) == 1
    s.stop_thread_executor()


def test_start_goals_and_wait_with_exception():
    class ErrorGoal(Goal):
        def on_enter(self):
            pass

        def tick(self):
            raise RuntimeError("boom")

    g = ErrorGoal(name="err", max_duration=0.01)
    s = Scenario(name="s", broker=None, goals=[g])
    futures = s.start_goals_and_wait()
    assert len(futures) == 1
    s.stop_thread_executor()


# --- start_fatal_goals ---


def test_start_fatal_goals():
    fg = MockGoal(complete_on_enter=True, name="fg1")
    s = Scenario(name="s", broker=None, fatal_goals=[fg])
    s.start_fatal_goals()
    s.stop_thread_executor(wait=True)


# --- start_antigoals ---


def test_start_antigoals():
    ag = MockGoal(complete_on_enter=True, name="ag1")
    s = Scenario(name="s", broker=None, anti_goals=[ag])
    s.start_antigoals()
    s.stop_thread_executor(wait=True)


# --- run_seq (mocked to avoid real broker) ---


def test_run_seq_no_broker():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    s = Scenario(name="s", broker=None, goals=[g1])
    with patch.object(s, "start_entities"):
        s.run_seq()
    assert g1.state in (GoalState.COMPLETED, GoalState.TERMINATED)


def test_run_seq_fatal_breaks():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    g2 = MockGoal(complete_on_enter=True, name="g2")
    fg = MockGoal(complete_on_enter=True, name="fg")
    fg.set_state(GoalState.COMPLETED)
    fg._ts_start = 0
    fg._ts_exit = 1
    s = Scenario(name="s", broker=None, goals=[g1, g2], fatal_goals=[fg])
    with (
        patch.object(s, "start_entities"),
        patch.object(s, "start_fatal_goals"),
        patch.object(s, "start_antigoals"),
    ):
        s.run_seq()


# --- run_concurrent (mocked to avoid real broker) ---


def test_run_concurrent_no_broker():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    s = Scenario(name="s", broker=None, goals=[g1])
    with patch.object(s, "start_entities"):
        s.run_concurrent()
    assert g1.state in (GoalState.COMPLETED, GoalState.TERMINATED)


# --- add_goal weight initialization ---


def test_add_goal_weight_initializes_list():
    s = Scenario(name="s", broker=None)
    s._goal_weights = None
    g = MockGoal(name="g1")
    s.add_goal(g, weight=0.7)
    assert 0.7 in s._goal_weights


# --- _create_comm_node ---


def test_create_comm_node_redis():
    from goalee.brokers import RedisBroker

    with patch.dict("sys.modules", {"commlib.transports.redis": MagicMock()}):  # noqa: SIM117
        with patch("goalee.scenario.Node") as MockNode:
            MockNode.return_value = MagicMock()
            s = Scenario(name="s", broker=RedisBroker())
            assert s._node is not None
            MockNode.assert_called_once()


def test_create_comm_node_mqtt():
    from goalee.brokers import MQTTBroker

    s = Scenario(name="s", broker=None)
    with patch.dict("sys.modules", {"commlib.transports.mqtt": MagicMock()}):  # noqa: SIM117
        with patch("goalee.scenario.Node") as MockNode:
            MockNode.return_value = MagicMock()
            result = s._create_comm_node(MQTTBroker())
            assert result is not None
            MockNode.assert_called_once()


def test_creation_with_broker_creates_node():
    from goalee.brokers import RedisBroker

    with patch.object(
        Scenario, "_create_comm_node", return_value=MagicMock()
    ) as mock_create:
        s = Scenario(name="s", broker=RedisBroker())
        assert s._node is not None
        mock_create.assert_called_once()


# --- init_rtmonitor with node ---


def test_init_rtmonitor_with_node():
    s = Scenario(name="s", broker=None)
    mock_node = MagicMock()
    s._node = mock_node
    with patch("goalee.scenario.RTMonitor") as MockRTM:
        mock_rtm = MagicMock()
        MockRTM.return_value = mock_rtm
        g = MockGoal(name="g1")
        s._goals = [g]
        s.init_rtmonitor("etopic", "ltopic")
        assert s._rtmonitor is mock_rtm
        MockRTM.assert_called_once_with(mock_node, "etopic", "ltopic")


# --- send_scenario_started/update/finished with rtmonitor ---


def test_send_scenario_started_with_rtmonitor():
    s = Scenario(name="s", broker=None)
    mock_rtm = MagicMock()
    s._rtmonitor = mock_rtm
    s.send_scenario_started("sequential")
    mock_rtm.send_event.assert_called_once()


def test_send_scenario_update_with_rtmonitor():
    s = Scenario(name="s", broker=None)
    mock_rtm = MagicMock()
    s._rtmonitor = mock_rtm
    s.send_scenario_update("concurrent")
    mock_rtm.send_event.assert_called_once()


def test_send_scenario_finished_with_rtmonitor():
    s = Scenario(name="s", broker=None)
    mock_rtm = MagicMock()
    s._rtmonitor = mock_rtm
    s.send_scenario_finished("sequential")
    mock_rtm.send_event.assert_called_once()


# --- run_seq with node and rtmonitor ---


def test_run_seq_with_node_and_rtmonitor():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    s = Scenario(name="s", broker=None, goals=[g1])
    mock_node = MagicMock()
    s._node = mock_node
    mock_rtm = MagicMock()
    s._rtmonitor = mock_rtm
    with patch.object(s, "start_entities"), patch("goalee.scenario.time") as mock_time:
        mock_time.perf_counter_ns.return_value = 1000000
        s.run_seq()
    mock_node.run.assert_called_once()
    mock_node.stop.assert_called_once()
    assert mock_rtm.send_event.call_count >= 2


# --- run_concurrent with node and rtmonitor ---


def test_run_concurrent_with_node_and_rtmonitor():
    g1 = MockGoal(complete_on_enter=True, name="g1")
    s = Scenario(name="s", broker=None, goals=[g1])
    mock_node = MagicMock()
    s._node = mock_node
    mock_rtm = MagicMock()
    s._rtmonitor = mock_rtm
    with patch.object(s, "start_entities"), patch("goalee.scenario.time") as mock_time:
        mock_time.perf_counter_ns.return_value = 1000000
        s.run_concurrent()
    mock_node.run.assert_called_once()
    assert mock_rtm.send_event.call_count >= 2
