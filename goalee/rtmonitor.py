import logging
from typing import Any, Dict
from commlib.msg import PubSubMessage
from goalee.logging import default_logger as logger


class EventMsg(PubSubMessage):
    type: str
    data: Dict[str, Any]


class LogMsg(PubSubMessage):
    msg: str
    level: str = "INFO"


class RemoteLogHandler(logging.Handler):

    def __init__(self, rtmonitor) -> None:
        self.rtm = rtmonitor
        super().__init__()

    def emit(self, record) -> None:
        self.rtm.log(record.msg, record.levelname)


class RTMonitor:
    def __init__(self, comm_node, etopic, ltopic):
        self.node = comm_node
        epub = self.node.create_publisher(
            topic=etopic,
            msg_type=EventMsg
        )
        epub.run()
        lpub = self.node.create_publisher(
            topic=ltopic,
            msg_type=LogMsg
        )
        lpub.run()
        self.epub = epub
        self.lpub = lpub
        logger.addHandler(RemoteLogHandler(self))
        logger.info(f'[RTMonitor]: Initialized topics: events -> {etopic}, logs -> {ltopic}')

    def send_event(self, event):
        # logger.debug(f'[RTMonitor] Sending Event: {event}')
        self.epub.publish(event)

    def send_log(self, log_msg):
        # logger.debug(f'[RTMonitor] Sending Log: {log_msg}')
        self.lpub.publish(log_msg)

    def log(self, msg, level="INFO"):
        log_msg = LogMsg(msg=msg, level=level)
        self.send_log(log_msg)
