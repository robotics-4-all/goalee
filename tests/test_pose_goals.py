from __future__ import annotations

from goalee.brokers import RedisBroker
from goalee.entity import Entity
from goalee.goal import GoalState
from goalee.pose_goals import OrientationGoal, PoseGoal, PositionGoal
from goalee.types import Orientation, Point


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
# PoseGoal
# ---------------------------------------------------------------------------


class TestPoseGoal:
    def _make_goal(self, entity=None, deviation_pos=1.0, deviation_ori=0.5):
        if entity is None:
            entity = make_entity()
        return PoseGoal(
            entity=entity,
            position=Point(5.0, 5.0, 0.0),
            orientation=Orientation(0.0, 0.0, 0.0),
            deviation_pos=deviation_pos,
            deviation_ori=deviation_ori,
            name="pose1",
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "pose1"
        assert goal._position == Point(5.0, 5.0, 0.0)
        assert goal._orientation == Orientation(0.0, 0.0, 0.0)
        assert goal._deviation_pos == 1.0
        assert goal._deviation_ori == 0.5

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_tick_updates_last_state(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0, "z": 0.0}
        entity.attributes["orientation"] = {
            "x": 0.0,
            "y": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
        }
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_state["position"] == {"x": 5.0, "y": 5.0, "z": 0.0}

    def test_check_pose_no_position_returns(self):
        entity = make_entity()
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_position_x_none_returns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": None, "y": 5.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_position_y_none_returns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": None, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_no_orientation_returns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_orientation_x_none_returns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0, "z": 0.0}
        entity.attributes["orientation"] = {"x": None, "y": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_orientation_y_none_returns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.0, "y": 5.0, "z": 0.0}
        entity.attributes["orientation"] = {"x": 0.0, "y": None}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pose_within_deviation_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.5, "y": 5.5, "z": 0.5}
        entity.attributes["orientation"] = {
            "x": 0.1,
            "y": 0.1,
            "roll": 0.1,
            "pitch": 0.1,
            "yaw": 0.1,
        }
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_pose_outside_deviation_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 50.0, "y": 50.0, "z": 50.0}
        entity.attributes["orientation"] = {
            "x": 0.0,
            "y": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
        }
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING


# ---------------------------------------------------------------------------
# PositionGoal
# ---------------------------------------------------------------------------


class TestPositionGoal:
    def _make_goal(self, entity=None, deviation=1.0):
        if entity is None:
            entity = make_entity()
        return PositionGoal(
            entity=entity,
            position=Point(5.0, 5.0, 0.0),
            deviation=deviation,
            name="pos1",
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "pos1"
        assert goal._position == Point(5.0, 5.0, 0.0)
        assert goal._deviation == 1.0

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_check_pos_no_position_returns(self):
        entity = make_entity()
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pos_all_xyz_none_warns(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": None, "y": None, "z": None}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pos_within_deviation_completes(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 5.5, "y": 5.5, "z": 0.5}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_pos_outside_deviation_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 50.0, "y": 50.0, "z": 50.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_pos_on_boundary_stays_running(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 6.0, "y": 5.0, "z": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_tick_updates_last_state(self):
        entity = make_entity()
        entity.attributes["position"] = {"x": 1.0, "y": 2.0, "z": 3.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_state["position"] == {"x": 1.0, "y": 2.0, "z": 3.0}


# ---------------------------------------------------------------------------
# OrientationGoal
# ---------------------------------------------------------------------------


class TestOrientationGoal:
    def _make_goal(self, entity=None, deviation=0.5):
        if entity is None:
            entity = make_entity()
        return OrientationGoal(
            entity=entity,
            orientation=Orientation(0.0, 0.0, 0.0),
            deviation=deviation,
            name="ori1",
        )

    def test_creation(self):
        goal = self._make_goal()
        assert goal.name == "ori1"
        assert goal._orientation == Orientation(0.0, 0.0, 0.0)
        assert goal._deviation == 0.5

    def test_on_enter_no_crash(self):
        goal = self._make_goal()
        goal.on_enter()

    def test_check_ori_no_orientation_returns(self):
        entity = make_entity()
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_ori_all_none_returns(self):
        entity = make_entity()
        entity.attributes["orientation"] = {"roll": None, "pitch": None, "yaw": None}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_check_ori_within_deviation_completes(self):
        entity = make_entity()
        entity.attributes["orientation"] = {"roll": 0.1, "pitch": 0.1, "yaw": 0.1}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.COMPLETED

    def test_check_ori_outside_deviation_stays_running(self):
        entity = make_entity()
        entity.attributes["orientation"] = {"roll": 5.0, "pitch": 5.0, "yaw": 5.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING

    def test_tick_updates_last_state(self):
        entity = make_entity()
        entity.attributes["orientation"] = {"roll": 0.1, "pitch": 0.2, "yaw": 0.3}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal._last_state["orientation"] == {
            "roll": 0.1,
            "pitch": 0.2,
            "yaw": 0.3,
        }

    def test_check_ori_on_boundary_stays_running(self):
        entity = make_entity()
        entity.attributes["orientation"] = {"roll": 0.5, "pitch": 0.0, "yaw": 0.0}
        goal = self._make_goal(entity=entity)
        goal.set_state(GoalState.RUNNING)
        goal.tick()
        assert goal.state == GoalState.RUNNING
