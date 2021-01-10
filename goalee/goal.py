from abc import ABCMeta, abstractmethod
from enum import IntEnum

import time
import uuid

from commlib.node import Node


class GoalState(IntEnum):
    IDLE = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3


class Goal(metaclass=ABCMeta):
    state = GoalState.IDLE

    def __init__(self,
                 comm_node: Node,
                 event_emitter=None,
                 name: str = None,
                 max_duration: float = 10.0):
        self._comm_node = comm_node
        self._ee = event_emitter
        self._max_duration = max_duration
        if name is None or len(name) == 0:
            name = self._gen_random_name()
        self._name = name
        self.set_state(GoalState.IDLE)

    def set_state(self, state: GoalState):
        if state not in GoalState:
            raise ValueError('Not a valid state was given')
        self._state = state
        self._report_state()

    def _report_state(self):
        if self._state == GoalState.IDLE:
            state_str  = 'IDLE'
        elif self._state == GoalState.RUNNING:
            state_str  = 'RUNNING'
        elif self._state == GoalState.COMPLETED:
            state_str  = 'COMPLETED'
        elif self._state == GoalState.FAILED:
            state_str  = 'FAILED'
        print(f'[*] - Goal <{self._name}> entered {state_str} state')

    @abstractmethod
    def enter(self):
        pass

    def on_enter(self):
        print(f'[*] - Entering Goal <{self._name}:{self.__class__.__name__}>')
        self.set_state(GoalState.RUNNING)
        self.run_until_exit()

    def run_until_exit(self):
        ts_start = time.time()
        while self._state not in (GoalState.COMPLETED, GoalState.FAILED):
            time.sleep(0.001)
            elapsed = time.time() - ts_start
            if elapsed > self._max_duration:
                self.set_state(GoalState.FAILED)
                print(
                    f'[*] - Goal <{self._name}> exited due' + \
                    f' to timeout after {self._max_duration} seconds!')

    def set_comm_node(self, comm_node: Node):
        if not isinstance(comm_node, Node):
            raise ValueError('')
        self._comm_node = comm_node

    def _gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')


class TopicMessageReceivedGoal(Goal):

    def __init__(self,
                 topic: str,
                 comm_node: Node = None,
                 name: str = None,
                 event_emitter=None,
                 max_duration: float = 10.0):
        super().__init__(comm_node, event_emitter, name=name,
                         max_duration=max_duration)
        self._listening_topic = topic
        self._msg = None

    def enter(self):
        self._listener = self._comm_node.create_subscriber(
            topic=self._listening_topic, on_message=self._on_message
        )
        self._listener.run()
        self.on_enter()

    def _on_message(self, msg):
        self.set_state(GoalState.COMPLETED)
