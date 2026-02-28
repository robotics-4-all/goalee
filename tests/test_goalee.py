from __future__ import annotations

from unittest.mock import MagicMock, patch

import goalee
from goalee import AMQPBroker, Broker, Entity, MQTTBroker, RedisBroker, Scenario
from goalee.complex_goal import ComplexGoalAlgorithm
from goalee.goal import GoalState
from goalee.types import Orientation, Point


def test_version():
    assert isinstance(goalee.__version__, str)
    parts = goalee.__version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_public_imports():
    assert Scenario is not None
    assert Entity is not None
    assert Broker is not None
    assert RedisBroker is not None
    assert MQTTBroker is not None
    assert AMQPBroker is not None


def test_goal_state_enum():
    assert GoalState.IDLE == 0
    assert GoalState.RUNNING == 1
    assert GoalState.COMPLETED == 2
    assert GoalState.FAILED == 3
    assert GoalState.TERMINATED == 4


def test_broker_defaults():
    redis = RedisBroker()
    assert redis.host == "localhost"
    assert redis.port == 6379
    assert redis.db == 0

    mqtt = MQTTBroker()
    assert mqtt.host == "localhost"
    assert mqtt.port == 1883

    amqp = AMQPBroker()
    assert amqp.host == "localhost"
    assert amqp.port == 5672
    assert amqp.vhost == "/"


def test_complex_goal_algorithm_enum():
    assert ComplexGoalAlgorithm.ALL_ACCOMPLISHED == 0
    assert ComplexGoalAlgorithm.NONE_ACCOMPLISHED == 2
    assert ComplexGoalAlgorithm.AT_LEAST_ONE_ACCOMPLISHED == 3


def test_point_operations():
    p1 = Point(1.0, 2.0, 3.0)
    p2 = Point(4.0, 5.0, 6.0)
    result = p1 + p2
    assert result.x == 5.0
    assert result.y == 7.0
    assert result.z == 9.0

    diff = p2 - p1
    assert diff.x == 3.0
    assert diff.y == 3.0
    assert diff.z == 3.0


def test_orientation_operations():
    o1 = Orientation(0.1, 0.2, 0.3)
    o2 = Orientation(0.4, 0.5, 0.6)
    result = o1 + o2
    assert abs(result.roll - 0.5) < 1e-9
    assert abs(result.pitch - 0.7) < 1e-9
    assert abs(result.yaw - 0.9) < 1e-9


def test_scenario_creation():
    broker = RedisBroker()
    with patch.object(Scenario, "_create_comm_node", return_value=MagicMock()):
        scenario = Scenario(name="test_scenario", broker=broker)
    assert scenario.name == "test_scenario"


def test_entity_creation():
    broker = RedisBroker()
    entity = Entity(
        name="test_entity",
        etype="sensor",
        topic="test.topic",
        attributes=["temp", "humidity"],
        source=broker,
    )
    assert entity.name == "test_entity"
    assert entity.topic == "test.topic"
    assert entity.attributes["temp"] is None
    assert entity.attributes["humidity"] is None
