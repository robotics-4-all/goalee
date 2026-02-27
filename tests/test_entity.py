from __future__ import annotations

from collections import deque
from unittest.mock import MagicMock, patch

import pytest

from goalee.brokers import AMQPBroker, MQTTBroker, RedisBroker
from goalee.entity import Entity


class TestEntityCreation:
    def test_basic_creation(self):
        broker = RedisBroker()
        e = Entity(
            name="sensor1",
            etype="sensor",
            topic="sensors.temp",
            attributes=["temp", "humidity"],
            source=broker,
        )
        assert e.name == "sensor1"
        assert e.etype == "sensor"
        assert e.topic == "sensors.temp"
        assert e.source is broker
        assert e._strict is False
        assert e._initialized is False
        assert e._started is False

    def test_attributes_initialized_to_none(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a", "b", "c"])
        assert e.attributes == {"a": None, "b": None, "c": None}

    def test_init_buffers_true(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a", "b"],
            init_buffers=True,
            buffer_length=5,
        )
        assert isinstance(e.attributes_buff["a"], deque)
        assert e.attributes_buff["a"].maxlen == 5
        assert isinstance(e.attributes_buff["b"], deque)
        assert e.attributes_buff["b"].maxlen == 5

    def test_init_buffers_false(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a", "b"])
        assert e.attributes_buff["a"] is None
        assert e.attributes_buff["b"] is None

    def test_strict_mode(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            strict_mode=True,
        )
        assert e._strict is True


class TestEntityGetItem:
    def test_getitem(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["temp"])
        e.attributes["temp"] = 25.0
        assert e["temp"] == 25.0

    def test_getitem_none(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["temp"])
        assert e["temp"] is None


class TestEntityGetAttr:
    def test_get_attr(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["temp"])
        e.attributes["temp"] = 42.0
        assert e.get_attr("temp") == 42.0


class TestEntityToCamelCase:
    def test_snake_to_camel(self):
        e = Entity(name="my_entity_name", etype="t", topic="t", attributes=[])
        assert e.camel_name == "MyEntityName"
        assert e.to_camel_case("my_entity") == "MyEntity"

    def test_single_word(self):
        e = Entity(name="sensor", etype="t", topic="t", attributes=[])
        assert e.camel_name == "Sensor"

    def test_already_camel(self):
        e = Entity(name="MySensor", etype="t", topic="t", attributes=[])
        assert e.camel_name == "Mysensor"


class TestEntityInitialized:
    def test_initially_false(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"])
        assert e.initialized is False

    def test_true_after_update(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"])
        e.update_state({"a": 1})
        assert e.initialized is True


class TestEntityUpdateState:
    def test_updates_attributes(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a", "b"])
        e.update_state({"a": 10, "b": 20})
        assert e.attributes["a"] == 10
        assert e.attributes["b"] == 20
        assert e._initialized is True

    def test_unknown_key_non_strict_continues(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"])
        e.update_state({"a": 10, "unknown": 99})
        assert e.attributes["a"] == 10
        assert e._initialized is True

    def test_unknown_key_strict_drops(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            strict_mode=True,
        )
        e.update_state({"a": 10, "unknown": 99})
        assert e.attributes["a"] is None
        assert e._initialized is False


class TestEntityUpdateAttributes:
    def test_updates_known_keys(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["x", "y"])
        e.update_attributes({"x": 1, "y": 2})
        assert e.attributes["x"] == 1
        assert e.attributes["y"] == 2

    def test_ignores_unknown_keys(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["x"])
        e.update_attributes({"x": 1, "z": 99})
        assert e.attributes["x"] == 1
        assert "z" not in e.attributes


class TestEntityUpdateBuffers:
    def test_appends_to_buffer(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            init_buffers=True,
            buffer_length=3,
        )
        e.update_buffers({"a": 1})
        e.update_buffers({"a": 2})
        assert list(e.attributes_buff["a"]) == [1, 2]

    def test_no_append_when_buffer_none(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"])
        e.update_buffers({"a": 1})
        assert e.attributes_buff["a"] is None

    def test_strict_mode_drops_invalid(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            init_buffers=True,
            strict_mode=True,
        )
        e.update_buffers({"a": 1, "bad": 2})
        assert len(e.attributes_buff["a"]) == 0


class TestEntityGetBuffer:
    def test_get_buffer_full(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            init_buffers=True,
            buffer_length=3,
        )
        e.attributes_buff["a"].append(1)
        e.attributes_buff["a"].append(2)
        e.attributes_buff["a"].append(3)
        result = e.get_buffer("a")
        assert result == [1, 2, 3]

    def test_get_buffer_with_size(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            init_buffers=True,
            buffer_length=5,
        )
        for i in range(5):
            e.attributes_buff["a"].append(i)
        result = e.get_buffer("a", size=3)
        assert result == [2, 3, 4]

    def test_get_buffer_not_full_returns_zeros(self):
        e = Entity(
            name="e",
            etype="t",
            topic="t",
            attributes=["a"],
            init_buffers=True,
            buffer_length=5,
        )
        e.attributes_buff["a"].append(1)
        result = e.get_buffer("a")
        assert result == [0] * 5


class TestEntityInitAttrBuffer:
    def test_creates_deque(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"])
        e.init_attr_buffer("a", 10)
        assert isinstance(e.attributes_buff["a"], deque)
        assert e.attributes_buff["a"].maxlen == 10


class TestEntityCreateNode:
    def test_no_source_raises(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=None)
        with pytest.raises(ValueError, match="not assigned a broker"):
            e.create_node()

    def test_invalid_broker_type_raises(self):
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source="invalid")
        with pytest.raises(ValueError, match="Invalid broker type"):
            e.create_node()

    @patch("goalee.entity.Node")
    def test_redis_broker(self, mock_node_cls):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        broker = RedisBroker(host="redis-host", port=6380, db=1)
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=broker)

        with patch.dict("sys.modules", {"commlib.transports.redis": MagicMock()}):
            e.create_node()

        assert e.node is mock_node
        mock_node.create_subscriber.assert_called_once()

    @patch("goalee.entity.Node")
    def test_amqp_broker(self, mock_node_cls):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        broker = AMQPBroker(host="amqp-host", port=5673)
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=broker)

        with patch.dict("sys.modules", {"commlib.transports.amqp": MagicMock()}):
            e.create_node()

        assert e.node is mock_node

    @patch("goalee.entity.Node")
    def test_mqtt_broker(self, mock_node_cls):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        broker = MQTTBroker(host="mqtt-host", port=1884)
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=broker)

        with patch.dict("sys.modules", {"commlib.transports.mqtt": MagicMock()}):
            e.create_node()

        assert e.node is mock_node


class TestEntityStart:
    @patch("goalee.entity.Node")
    def test_start_sets_started(self, mock_node_cls):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        broker = RedisBroker()
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=broker)

        with patch.dict("sys.modules", {"commlib.transports.redis": MagicMock()}):
            e.start()

        assert e._started is True
        mock_node.run.assert_called_once()

    @patch("goalee.entity.Node")
    def test_start_twice_is_noop(self, mock_node_cls):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        broker = RedisBroker()
        e = Entity(name="e", etype="t", topic="t", attributes=["a"], source=broker)

        with patch.dict("sys.modules", {"commlib.transports.redis": MagicMock()}):
            e.start()
            e.start()

        mock_node.run.assert_called_once()
