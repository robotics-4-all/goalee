from __future__ import annotations

import pytest

from goalee.brokers import RedisBroker
from goalee.entity import Entity
from goalee.entity_goals import (
    AttrStreamStrategy,
    EntityAttrStream,
    EntityStateChange,
    EntityStateCondition,
)
from goalee.goal import GoalState


def make_entity(name="test_entity", attrs=None, source=None):
    attrs = attrs or ["position", "orientation"]
    source = source or RedisBroker()
    return Entity(
        name=name,
        etype="sensor",
        topic=f"{name}.topic",
        attributes=attrs,
        source=source,
    )


# ---------------------------------------------------------------------------
# EntityStateChange
# ---------------------------------------------------------------------------


class TestEntityStateChange:
    def test_creation(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc1")
        assert goal.name == "sc1"
        assert goal.state == GoalState.IDLE
        assert goal._last_state == entity.attributes

    def test_creation_with_durations(self):
        entity = make_entity()
        goal = EntityStateChange(
            entity, name="sc2", max_duration=10.0, min_duration=1.0, for_duration=5.0
        )
        assert goal._max_duration == 10.0
        assert goal._min_duration == 1.0
        assert goal._for_duration == 5.0

    def test_on_enter_no_crash(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc3")
        goal.on_enter()

    def test_tick_state_change_completes(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc4")
        goal.set_state(GoalState.RUNNING)
        entity.attributes["position"] = {"x": 1.0, "y": 2.0}
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_no_state_change_stays_running(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc5")
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_tick_state_change_with_for_duration_sets_ts_hold(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc6", for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        entity.attributes["position"] = {"x": 1.0, "y": 2.0}
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING

    def test_tick_for_duration_completes_after_elapsed(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc7", for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        entity.attributes["position"] = {"x": 1.0, "y": 2.0}
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_state_changes_back_before_for_duration(self):
        entity = make_entity()
        goal = EntityStateChange(entity, name="sc8", for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        entity.attributes["position"] = {"x": 1.0, "y": 2.0}
        goal.tick()
        assert goal._ts_hold == 100.0
        goal.get_current_ts = lambda: 102.0
        goal.tick()
        assert goal.state == GoalState.RUNNING


# ---------------------------------------------------------------------------
# EntityStateCondition
# ---------------------------------------------------------------------------


class TestEntityStateCondition:
    def test_creation_with_lambda(self):
        entity = make_entity()

        def cond(e):
            return e["test_entity"]["position"] is not None

        goal = EntityStateCondition([entity], name="cond1", condition=cond)
        assert goal.name == "cond1"
        assert goal._condition is cond

    def test_on_enter_sets_ts_hold(self):
        entity = make_entity()
        goal = EntityStateCondition([entity], name="cond2", condition=lambda e: True)
        goal.on_enter()
        assert goal._ts_hold == -1.0

    def test_get_entities_map(self):
        e1 = make_entity("e1")
        e2 = make_entity("e2")
        goal = EntityStateCondition([e1, e2], name="cond3", condition=lambda e: True)
        emap = goal.get_entities_map()
        assert emap == {"e1": e1, "e2": e2}

    def test_tick_lambda_true_completes(self):
        entity = make_entity()
        goal = EntityStateCondition([entity], name="cond4", condition=lambda e: True)
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_lambda_false_stays_running(self):
        entity = make_entity()
        goal = EntityStateCondition([entity], name="cond5", condition=lambda e: False)
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.RUNNING
        assert goal._ts_hold == -1.0

    def test_tick_callable_condition(self):
        entity = make_entity()

        class MyCallable:
            def __call__(self, entities):
                return True

        goal = EntityStateCondition([entity], name="cond6", condition=MyCallable())
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_string_condition_true(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = 10
        goal = EntityStateCondition(
            [entity],
            name="cond7",
            condition='entities["test_entity"]["value"] > 5',
        )
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_string_condition_false(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = 3
        goal = EntityStateCondition(
            [entity],
            name="cond8",
            condition='entities["test_entity"]["value"] > 5',
        )
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_tick_with_for_duration(self):
        entity = make_entity()
        goal = EntityStateCondition(
            [entity], name="cond9", condition=lambda e: True, for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_for_duration_resets_on_false(self):
        call_count = 0

        def alternating_cond(e):
            nonlocal call_count
            call_count += 1
            return call_count <= 1

        entity = make_entity()
        goal = EntityStateCondition(
            [entity], name="cond10", condition=alternating_cond, for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        goal.tick()
        assert goal._ts_hold == -1.0

    def test_tick_type_error_caught(self):
        entity = make_entity()
        goal = EntityStateCondition(
            [entity],
            name="cond11",
            condition=lambda e: e["test_entity"]["position"] + 5,
        )
        goal.set_state(GoalState.RUNNING)
        goal.on_enter()
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_evaluate_condition_true(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = 10
        goal = EntityStateCondition(
            [entity],
            name="cond12",
            condition='entities["test_entity"]["value"] == 10',
        )
        result = goal.evaluate_condition(goal.get_entities_map())
        assert result is True

    def test_evaluate_condition_false(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = 3
        goal = EntityStateCondition(
            [entity],
            name="cond13",
            condition='entities["test_entity"]["value"] == 10',
        )
        result = goal.evaluate_condition(goal.get_entities_map())
        assert result is False

    def test_evaluate_condition_nonetype_exception(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = None
        goal = EntityStateCondition(
            [entity],
            name="cond14",
            condition='entities["test_entity"]["value"] > 5',
        )
        result = goal.evaluate_condition(goal.get_entities_map())
        assert result is False

    def test_evaluate_condition_other_exception(self):
        entity = make_entity(attrs=["value"])
        entity.attributes["value"] = 10
        goal = EntityStateCondition(
            [entity],
            name="cond15",
            condition="undefined_var + 1",
        )
        result = goal.evaluate_condition(goal.get_entities_map())
        assert result is False

    def test_evaluate_condition_with_builtin_functions(self):
        entity = make_entity(attrs=["values"])
        entity.attributes["values"] = [1, 2, 3, 4, 5]
        goal = EntityStateCondition(
            [entity],
            name="cond16",
            condition='mean(entities["test_entity"]["values"]) > 2',
        )
        result = goal.evaluate_condition(goal.get_entities_map())
        assert result is True


# ---------------------------------------------------------------------------
# AttrStreamStrategy enum
# ---------------------------------------------------------------------------


class TestAttrStreamStrategy:
    def test_all_values(self):
        assert AttrStreamStrategy.ALL == 0
        assert AttrStreamStrategy.NONE == 1
        assert AttrStreamStrategy.AT_LEAST_ONE == 2
        assert AttrStreamStrategy.JUST_ONE == 3
        assert AttrStreamStrategy.EXACTLY_X == 4
        assert AttrStreamStrategy.ALL_ORDERED == 5
        assert AttrStreamStrategy.EXACTLY_X_ORDERED == 6


# ---------------------------------------------------------------------------
# EntityAttrStream
# ---------------------------------------------------------------------------


class TestEntityAttrStream:
    def _make_stream_entity(self, name="stream_entity"):
        return make_entity(name=name, attrs=["temperature"])

    def test_creation(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20, 30], AttrStreamStrategy.ALL, name="stream1"
        )
        assert goal.name == "stream1"
        assert goal._attr == "temperature"
        assert goal._value == [10, 20, 30]
        assert goal._strategy == AttrStreamStrategy.ALL
        assert goal._value_check_list == [False, False, False]
        assert goal._last_state is None

    def test_on_enter_no_crash(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10], AttrStreamStrategy.ALL, name="stream2"
        )
        goal.on_enter()

    def test_tick_first_initializes_last_state(self):
        entity = self._make_stream_entity()
        entity.attributes["temperature"] = 10
        goal = EntityAttrStream(
            entity, "temperature", [10], AttrStreamStrategy.ALL, name="stream3"
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_state is not None
        assert goal._last_state["temperature"] == 10

    def test_tick_attr_matches_value(self):
        entity = self._make_stream_entity()
        entity.attributes["temperature"] = 5
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.AT_LEAST_ONE,
            name="stream4",
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._value_check_list == [False, False]
        entity.attributes["temperature"] = 10
        goal.tick()
        assert goal._value_check_list == [True, False]
        assert goal.state == GoalState.COMPLETED

    def test_tick_no_change_returns_early(self):
        entity = self._make_stream_entity()
        entity.attributes["temperature"] = 5
        goal = EntityAttrStream(
            entity, "temperature", [5], AttrStreamStrategy.NONE, name="stream5"
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        initial_check = goal._value_check_list.copy()
        goal.tick()
        assert goal._value_check_list == initial_check

    def test_tick_attr_not_in_entity_raises(self):
        entity = self._make_stream_entity()
        entity.attributes["temperature"] = 5
        goal = EntityAttrStream(
            entity, "missing_attr", [5], AttrStreamStrategy.ALL, name="stream6"
        )
        goal.set_state(GoalState.RUNNING)
        with pytest.raises(ValueError, match="Attribute missing_attr not found"):
            goal.tick()

    def test_is_done_all_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20], AttrStreamStrategy.ALL, name="stream7"
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, True]
        assert goal.is_done() is True

    def test_is_done_none_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20], AttrStreamStrategy.NONE, name="stream8"
        )
        assert goal.is_done() is True
        goal._value_check_list = [True, False]
        assert goal.is_done() is False

    def test_is_done_at_least_one_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.AT_LEAST_ONE,
            name="stream9",
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, False]
        assert goal.is_done() is True

    def test_is_done_just_one_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.JUST_ONE,
            name="stream10",
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, False]
        assert goal.is_done() is True
        goal._value_check_list = [True, True]
        assert goal.is_done() is False

    def test_is_done_exactly_x_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.EXACTLY_X,
            name="stream11",
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, True]
        assert goal.is_done() is True

    def test_is_done_all_ordered_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.ALL_ORDERED,
            name="stream12",
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, True]
        assert goal.is_done() is True

    def test_is_done_exactly_x_ordered_strategy(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.EXACTLY_X_ORDERED,
            name="stream13",
        )
        assert goal.is_done() is False
        goal._value_check_list = [True, True]
        assert goal.is_done() is True

    def test_process_for_ordered_strategy_resets_on_out_of_order(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20, 30],
            AttrStreamStrategy.ALL_ORDERED,
            name="stream14",
        )
        goal._value_check_list = [False, False, True]
        goal.process_for_ordered_strategy()
        assert goal._value_check_list == [False, False, False]

    def test_process_for_ordered_strategy_keeps_in_order(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20, 30],
            AttrStreamStrategy.ALL_ORDERED,
            name="stream15",
        )
        goal._value_check_list = [True, True, False]
        goal.process_for_ordered_strategy()
        assert goal._value_check_list == [True, True, False]

    def test_reset_check_list(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20, 30], AttrStreamStrategy.ALL, name="stream16"
        )
        goal._value_check_list = [True, True, True]
        goal.reset_check_list()
        assert goal._value_check_list == [False, False, False]

    def test_tick_all_strategy_completes(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20], AttrStreamStrategy.ALL, name="stream17"
        )
        goal.set_state(GoalState.RUNNING)
        entity.attributes["temperature"] = 10
        goal.tick()
        assert goal.state == GoalState.RUNNING
        entity.attributes["temperature"] = 20
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_none_strategy_completes_initially(self):
        entity = self._make_stream_entity()
        entity.attributes["temperature"] = 99
        goal = EntityAttrStream(
            entity, "temperature", [10, 20], AttrStreamStrategy.NONE, name="stream18"
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_tick_ordered_strategy_out_of_order_resets(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20, 30],
            AttrStreamStrategy.ALL_ORDERED,
            name="stream19",
        )
        goal.set_state(GoalState.RUNNING)
        entity.attributes["temperature"] = 20
        goal.tick()
        assert goal._value_check_list == [False, False, False]

    def test_tick_ordered_strategy_in_order_completes(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity,
            "temperature",
            [10, 20],
            AttrStreamStrategy.ALL_ORDERED,
            name="stream20",
        )
        goal.set_state(GoalState.RUNNING)
        entity.attributes["temperature"] = 10
        goal.tick()
        assert goal._value_check_list == [True, False]
        entity.attributes["temperature"] = 20
        goal.tick()
        assert goal._value_check_list == [True, True]
        assert goal.state == GoalState.COMPLETED

    def test_tick_already_checked_value_skipped(self):
        entity = self._make_stream_entity()
        goal = EntityAttrStream(
            entity, "temperature", [10, 20], AttrStreamStrategy.ALL, name="stream21"
        )
        goal.set_state(GoalState.RUNNING)
        entity.attributes["temperature"] = 10
        goal.tick()
        assert goal._value_check_list == [True, False]
        entity.attributes["temperature"] = 99
        goal.tick()
        entity.attributes["temperature"] = 10
        goal.tick()
        assert goal._value_check_list == [True, False]
