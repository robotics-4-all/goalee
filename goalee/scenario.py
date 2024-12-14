from abc import ABCMeta, abstractmethod
from enum import IntEnum
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Optional

from commlib.node import Node
from goalee.goal import Goal
from goalee.brokers import Broker


class Scenario:
    def __init__(self,
                 name: str = "",
                 broker: Optional[Broker] = None,
                 score_weights: Optional[List] = None):
        self._broker = broker
        if name in (None, "") or len(name) == 0:
            name = self.gen_random_name()
        self._name = name
        self._score_weights = score_weights
        if self._broker is not None:
            self._input_node = self._create_comm_node(self._broker)
        else:
            self._input_node = None
        self._goals = []
        self._entities = []

    def gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')

    def _create_comm_node(self, broker):
        if broker.__class__.__name__ == 'RedisBroker':
            from commlib.transports.redis import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                db=broker.db,
                username=broker.username,
                password=broker.password
            )
        elif broker.__class__.__name__ == 'AMQPBroker':
            from commlib.transports.amqp import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                vhost=broker.vhost,
                username=broker.username,
                password=broker.password
            )
        elif broker.__class__.__name__ == 'MQTTBroker':
            from commlib.transports.mqtt import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                username=broker.username,
                password=broker.password
            )
        node = Node(node_name=self._name,
                    connection_params=conn_params,
                    debug=False)
        return node

    def add_goal(self, goal: Goal):
        self._goals.append(goal)

    def create_entities(self):
        for goal in self._goals:
            for entity in goal.entities:
                if self._broker is not None:
                    entity.broker = self._broker
                entity.start()

    def run_seq(self):
        self.create_entities()
        for g in self._goals:
            g.enter()
        print(
            f'Finished Scenario <{self._name}> in Ordered/Sequential Mode')
        score = self.calc_score()
        print(f'Results for Scenario <{self._name}>: {self.make_result_list()}')
        print(f'Score for Scenario <{self._name}>: {score}')

    def run_concurrent(self):
        self.create_entities()
        n_threads = len(self._goals)
        features = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            feature = executor.submit(goal.enter, )
            features.append(feature)
        for f in as_completed(features):
            pass
        print(f'Finished Scenario <{self._name}> in Concurrent Mode')
        score = self.calc_score()
        print(f'Results for Scenario <{self._name}>: {self.make_result_list()}')
        print(f'Score for Scenario <{self._name}>: {score}')

    def make_result_list(self):
        res_list = [(goal.name, goal.status) for goal in self._goals]
        return res_list

    def calc_score(self):
        if self._score_weights is None:
            self._score_weights = [1/len(self._goals)] * len(self._goals)
        res = [goal.status * w for goal,w in zip(self._goals,
                                                 self._score_weights)]
        res = sum(res)
        return res
