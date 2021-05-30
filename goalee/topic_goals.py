from typing import Any, Optional, Callable
from enum import IntEnum

import time
import uuid

from commlib.node import Node

from goalee.goal import Goal, GoalState


class TopicMessageReceivedGoal(Goal):

    def __init__(self,
                 topic: str,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._listening_topic = topic
        self._msg = None

    def on_enter(self):
        self._listener = self._comm_node.create_subscriber(
            topic=self._listening_topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        self.set_state(GoalState.COMPLETED)


class TopicMessageParamGoal(Goal):

    def __init__(self,
                 topic: str,
                 comm_node: Optional[Node] = None,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 condition: Optional[Callable] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._listening_topic = topic
        self._msg = None
        self._condition = condition

    def on_enter(self):
        self._listener = self._comm_node.create_subscriber(
            topic=self._listening_topic, on_message=self._on_message
        )
        self._listener.run()

    def on_exit(self):
        self._listener.stop()

    def _on_message(self, msg):
        if self._condition(msg):
            self.set_state(GoalState.COMPLETED)
