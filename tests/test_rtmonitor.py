from __future__ import annotations

import logging
from unittest.mock import MagicMock

from goalee.rtmonitor import EventMsg, LogMsg, RemoteLogHandler, RTMonitor


class TestEventMsg:
    def test_creation(self):
        msg = EventMsg(type="goal_state", data={"key": "value"})
        assert msg.type == "goal_state"
        assert msg.data == {"key": "value"}

    def test_empty_data(self):
        msg = EventMsg(type="test", data={})
        assert msg.data == {}


class TestLogMsg:
    def test_default_level(self):
        msg = LogMsg(msg="hello")
        assert msg.msg == "hello"
        assert msg.level == "INFO"

    def test_custom_level(self):
        msg = LogMsg(msg="error occurred", level="ERROR")
        assert msg.level == "ERROR"

    def test_warning_level(self):
        msg = LogMsg(msg="warning", level="WARNING")
        assert msg.level == "WARNING"


class TestRemoteLogHandler:
    def test_emit_calls_rtmonitor_log(self):
        mock_rtm = MagicMock()
        handler = RemoteLogHandler(mock_rtm)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
        mock_rtm.log.assert_called_once_with("test message", "INFO")

    def test_emit_handles_exception(self):
        mock_rtm = MagicMock()
        mock_rtm.log.side_effect = RuntimeError("connection failed")
        handler = RemoteLogHandler(mock_rtm)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    def test_is_logging_handler(self):
        mock_rtm = MagicMock()
        handler = RemoteLogHandler(mock_rtm)
        assert isinstance(handler, logging.Handler)


class TestRTMonitor:
    def _make_rtmonitor(self):
        mock_node = MagicMock()
        mock_pub = MagicMock()
        mock_node.create_publisher.return_value = mock_pub
        rtm = RTMonitor(mock_node, "events.topic", "logs.topic")
        return rtm, mock_node, mock_pub

    def test_init_creates_publishers(self):
        mock_node = MagicMock()
        mock_pub = MagicMock()
        mock_node.create_publisher.return_value = mock_pub
        rtm = RTMonitor(mock_node, "events", "logs")
        assert mock_node.create_publisher.call_count == 2
        assert mock_pub.run.call_count == 2
        assert rtm.epub is mock_pub
        assert rtm.lpub is mock_pub

    def test_send_event(self):
        rtm, _, mock_pub = self._make_rtmonitor()
        event = EventMsg(type="test", data={"a": 1})
        rtm.send_event(event)
        mock_pub.publish.assert_called_with(event)

    def test_send_log(self):
        rtm, _, mock_pub = self._make_rtmonitor()
        log_msg = LogMsg(msg="hello", level="DEBUG")
        rtm.send_log(log_msg)
        mock_pub.publish.assert_called_with(log_msg)

    def test_log_creates_and_sends(self):
        rtm, _, mock_pub = self._make_rtmonitor()
        rtm.log("test message", "WARNING")
        call_args = mock_pub.publish.call_args
        sent_msg = call_args[0][0]
        assert isinstance(sent_msg, LogMsg)
        assert sent_msg.msg == "test message"
        assert sent_msg.level == "WARNING"

    def test_log_default_level(self):
        rtm, _, mock_pub = self._make_rtmonitor()
        rtm.log("info message")
        call_args = mock_pub.publish.call_args
        sent_msg = call_args[0][0]
        assert sent_msg.level == "INFO"

    def test_init_adds_remote_log_handler(self):
        mock_node = MagicMock()
        mock_pub = MagicMock()
        mock_node.create_publisher.return_value = mock_pub
        from goalee.logging import default_logger

        initial_handler_count = len(default_logger.handlers)
        RTMonitor(mock_node, "e", "l")
        assert len(default_logger.handlers) >= initial_handler_count
