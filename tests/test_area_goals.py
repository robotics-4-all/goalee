from __future__ import annotations

import math

from goalee.area_goals import (
    AreaGoalTag,
    CircularAreaGoal,
    MovingAreaGoal,
    RectangleAreaGoal,
)
from goalee.brokers import RedisBroker
from goalee.entity import Entity
from goalee.goal import GoalState
from goalee.types import Point


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
# AreaGoalTag enum
# ---------------------------------------------------------------------------


class TestAreaGoalTag:
    def test_values(self):
        assert AreaGoalTag.ENTER == 0
        assert AreaGoalTag.EXIT == 1
        assert AreaGoalTag.AVOID == 2
        assert AreaGoalTag.STEP == 3
        assert AreaGoalTag.STAY == 4
        assert AreaGoalTag.CROSS == 5


# ---------------------------------------------------------------------------
# RectangleAreaGoal
# ---------------------------------------------------------------------------


class TestRectangleAreaGoal:
    def _make_goal(self, entities=None, tag=AreaGoalTag.ENTER, for_duration=None):
        if entities is None:
            entities = [make_entity()]
        return RectangleAreaGoal(
            entities=entities,
            bottom_left_edge=Point(0.0, 0.0, 0.0),
            length_x=10.0,
            length_y=10.0,
            tag=tag,
            name="rect1",
            for_duration=for_duration,
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "rect1"
        assert goal.state == GoalState.IDLE
        assert goal._bottom_left_edge == Point(0.0, 0.0, 0.0)
        assert goal._length_x == 10.0
        assert goal._length_y == 10.0

    def test_tag_property(self):
        goal = self._make_goal(tag=AreaGoalTag.AVOID)
        assert goal.tag == AreaGoalTag.AVOID

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_tick_updates_last_states(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_states[0]["position"] == {"x": 5.0, "y": 5.0}

    def test_check_area_inside_enter_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_outside_enter_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 15.0, "y": 15.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_inside_avoid_fails(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], tag=AreaGoalTag.AVOID)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_position_none_skips(self):
        entity = make_entity()
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_pos_x_none_skips(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": None, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_pos_y_none_skips(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": None}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_enter_with_for_duration_sets_ts_hold(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING

    def test_check_area_enter_for_duration_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_avoid_with_for_duration_sets_ts_hold(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(
            entities=[entity], tag=AreaGoalTag.AVOID, for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING

    def test_check_area_avoid_for_duration_fails(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(
            entities=[entity], tag=AreaGoalTag.AVOID, for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_leaves_area_resets_ts_hold(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        entity.attributes["position"] = {"x": 15.0, "y": 15.0}
        goal.tick()
        assert goal._ts_hold == -1.0

    def test_check_area_on_boundary_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 0.0, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING


# ---------------------------------------------------------------------------
# CircularAreaGoal
# ---------------------------------------------------------------------------


class TestCircularAreaGoal:
    def _make_goal(self, entities=None, tag=AreaGoalTag.ENTER, for_duration=None):
        if entities is None:
            entities = [make_entity()]
        return CircularAreaGoal(
            entities=entities,
            center=Point(5.0, 5.0, 0.0),
            radius=3.0,
            tag=tag,
            name="circ1",
            for_duration=for_duration,
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "circ1"
        assert goal._center == Point(5.0, 5.0, 0.0)
        assert goal._radius == 3.0

    def test_tag_property(self):
        goal = self._make_goal(tag=AreaGoalTag.EXIT)
        assert goal.tag == AreaGoalTag.EXIT

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_check_area_inside_enter_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_outside_enter_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 50.0, "y": 50.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_inside_avoid_fails(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], tag=AreaGoalTag.AVOID)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_none_position_skips(self):
        entity = make_entity()
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_pos_x_none_skips(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": None, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_enter_with_for_duration(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_avoid_with_for_duration(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(
            entities=[entity], tag=AreaGoalTag.AVOID, for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_leaves_resets_ts_hold(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0}
        goal = self._make_goal(entities=[entity], for_duration=5.0)
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        entity.attributes["position"] = {"x": 50.0, "y": 50.0}
        goal.tick()
        assert goal._ts_hold == -1.0

    def test_calc_distance(self):
        goal = self._make_goal()
        pos = {"x": 8.0, "y": 9.0}
        expected = math.sqrt((8.0 - 5.0) ** 2 + (9.0 - 5.0) ** 2)
        assert goal._calc_distance(pos) == expected

    def test_tick_updates_states(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.0, "y": 1.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_states[0]["position"] == {"x": 1.0, "y": 1.0}

    def test_on_boundary_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 8.0, "y": 5.0}
        goal = self._make_goal(entities=[entity])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED


# ---------------------------------------------------------------------------
# MovingAreaGoal
# ---------------------------------------------------------------------------


class TestMovingAreaGoal:
    def _make_goal(
        self,
        motion_entity=None,
        entities=None,
        tag=AreaGoalTag.ENTER,
        for_duration=None,
    ):
        if motion_entity is None:
            motion_entity = make_entity("motion")
        if entities is None:
            monitor = make_entity("monitor")
            entities = [monitor]
        return MovingAreaGoal(
            motion_entity=motion_entity,
            entities=entities,
            radius=3.0,
            tag=tag,
            name="moving1",
            for_duration=for_duration,
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "moving1"
        assert goal._radius == 3.0

    def test_motion_entity_removed_from_entities(self):
        motion = make_entity("motion")
        monitor = make_entity("monitor")
        entities = [motion, monitor]
        goal = MovingAreaGoal(
            motion_entity=motion,
            entities=entities,
            radius=3.0,
            name="moving2",
        )
        assert motion not in goal._entities
        assert monitor in goal._entities

    def test_motion_entity_not_in_entities_no_error(self):
        motion = make_entity("motion")
        monitor = make_entity("monitor")
        goal = MovingAreaGoal(
            motion_entity=motion,
            entities=[monitor],
            radius=3.0,
            name="moving3",
        )
        assert motion not in goal._entities

    def test_motion_entity_property(self):
        motion = make_entity("motion")
        goal = self._make_goal(motion_entity=motion)
        assert goal.motion_entity is motion

    def test_tag_property(self):
        goal = self._make_goal(tag=AreaGoalTag.AVOID)
        assert goal.tag == AreaGoalTag.AVOID

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_check_area_motion_entity_state_none_returns(self):
        motion = make_entity("motion")
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 5.0, "y": 5.0}}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_motion_entity_state_empty_returns(self):
        motion = make_entity("motion")
        motion.state = {}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 5.0, "y": 5.0}}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_monitor_state_none_skips(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_monitor_state_empty_skips(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_no_position_key_warns(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"velocity": 1.0}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_position_within_radius_enter_completes(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 6.0, "y": 6.0}}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_position_outside_radius_enter_stays_running(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 50.0, "y": 50.0}}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_area_not_reached_avoid_fails(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 50.0, "y": 50.0}}
        goal = self._make_goal(
            motion_entity=motion, entities=[monitor], tag=AreaGoalTag.AVOID
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_enter_with_for_duration(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 6.0, "y": 6.0}}
        goal = self._make_goal(
            motion_entity=motion, entities=[monitor], for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        assert goal.state == GoalState.RUNNING
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_area_avoid_with_for_duration(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 50.0, "y": 50.0}}
        goal = self._make_goal(
            motion_entity=motion,
            entities=[monitor],
            tag=AreaGoalTag.AVOID,
            for_duration=5.0,
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        goal.get_current_ts = lambda: 106.0
        goal.tick()
        assert goal.state == GoalState.FAILED

    def test_check_area_leaves_area_resets_ts_hold(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 6.0, "y": 6.0}}
        goal = self._make_goal(
            motion_entity=motion, entities=[monitor], for_duration=5.0
        )
        goal.set_state(GoalState.RUNNING)
        goal.get_current_ts = lambda: 100.0
        goal.tick()
        assert goal._ts_hold == 100.0
        monitor.state = {"position": {"x": 50.0, "y": 50.0}}
        goal.tick()
        assert goal._ts_hold == -1.0

    def test_calc_distance(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        goal = self._make_goal(motion_entity=motion)
        pos = {"x": 8.0, "y": 9.0}
        expected = math.sqrt((8.0 - 5.0) ** 2 + (9.0 - 5.0) ** 2)
        assert goal._calc_distance(pos) == expected

    def test_check_area_pos_xy_none_warns(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": None, "y": None}}
        goal = self._make_goal(motion_entity=motion, entities=[monitor])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_reached_avoid_resets_ts_hold(self):
        motion = make_entity("motion")
        motion.state = {"position": {"x": 5.0, "y": 5.0}}
        monitor = make_entity("monitor")
        monitor.state = {"position": {"x": 6.0, "y": 6.0}}
        goal = self._make_goal(
            motion_entity=motion, entities=[monitor], tag=AreaGoalTag.AVOID
        )
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._ts_hold == -1.0
