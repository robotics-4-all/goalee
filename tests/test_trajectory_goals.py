from __future__ import annotations

from goalee.brokers import RedisBroker
from goalee.entity import Entity
from goalee.goal import GoalState
from goalee.trajectory_goals import WaypointTrajectoryGoal
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
# WaypointTrajectoryGoal
# ---------------------------------------------------------------------------


class TestWaypointTrajectoryGoal:
    def _make_goal(self, entity=None, waypoints=None, deviation=1.0):
        if entity is None:
            entity = make_entity()
        if waypoints is None:
            waypoints = [
                Point(1.0, 1.0, 0.0),
                Point(5.0, 5.0, 0.0),
                Point(10.0, 10.0, 0.0),
            ]
        return WaypointTrajectoryGoal(
            entity=entity,
            waypoints=waypoints,
            deviation=deviation,
            name="traj1",
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "traj1"
        assert len(goal._waypoints) == 3
        assert goal._deviation == 1.0
        assert goal._waypoints_reached_map == [False, False, False]

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_current_target_waypoint_returns_first_unreached(self):
        goal = self._make_goal()
        wp, idx = goal.current_target_waypoint()
        assert idx == 0
        assert wp == Point(1.0, 1.0, 0.0)

    def test_current_target_waypoint_skips_reached(self):
        goal = self._make_goal()
        goal._waypoints_reached_map[0] = True
        wp, idx = goal.current_target_waypoint()
        assert idx == 1
        assert wp == Point(5.0, 5.0, 0.0)

    def test_tick_updates_last_state(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.0, "y": 1.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_state["position"] == {"x": 1.0, "y": 1.0, "z": 0.0}

    def test_check_reached_no_position_returns(self):
        entity = make_entity()
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map == [False, False, False]
        assert goal.state == GoalState.RUNNING

    def test_check_reached_all_xyz_none_warns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": None, "y": None, "z": None}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map == [False, False, False]
        assert goal.state == GoalState.RUNNING

    def test_check_reached_first_waypoint(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.0, "y": 1.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map[0] is True
        assert goal._waypoints_reached_map[1] is False

    def test_check_reached_within_deviation(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.5, "y": 1.5, "z": 0.5}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map[0] is True

    def test_check_reached_outside_deviation(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 50.0, "y": 50.0, "z": 50.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map == [False, False, False]

    def test_tick_all_waypoints_reached_completes(self):
        entity = make_entity()
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)

        entity.attributes["position"] = {"x": 1.0, "y": 1.0, "z": 0.0}
        goal.tick()
        assert goal._waypoints_reached_map[0] is True
        assert goal.state == GoalState.RUNNING

        entity.attributes["position"] = {"x": 5.0, "y": 5.0, "z": 0.0}
        goal.tick()
        assert goal._waypoints_reached_map[1] is True
        assert goal.state == GoalState.RUNNING

        entity.attributes["position"] = {"x": 10.0, "y": 10.0, "z": 0.0}
        goal.tick()
        assert goal._waypoints_reached_map[2] is True
        assert goal.state == GoalState.COMPLETED

    def test_tick_not_all_reached_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.0, "y": 1.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_single_waypoint_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 3.0, "y": 3.0, "z": 0.0}
        goal = self._make_goal(entity=entity, waypoints=[Point(3.0, 3.0, 0.0)])
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_on_boundary_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 2.0, "y": 1.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._waypoints_reached_map[0] is False
