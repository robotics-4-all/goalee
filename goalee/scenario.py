import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from commlib.node import Node
from goalee.goal import Goal
from goalee.brokers import Broker
from goalee.logging import default_logger as logger
from goalee.rtmonitor import RTMonitor, EventMsg


class Scenario:
    def __init__(self,
                 name: str = "",
                 broker: Optional[Broker] = None,
                 score_weights: Optional[List] = None):
        self._broker = broker
        self._rtmonitor = None
        if name in (None, "") or len(name) == 0:
            name = self.gen_random_name()
        self._name = name
        self._score_weights = score_weights
        if self._broker is not None:
            self._node = self._create_comm_node(self._broker)
        else:
            self._node = None
        self._goals = []
        self._entities = []

    @property
    def name(self):
        return self._name

    def print_stats(self):
        self.log_info(f"Scenario '{self._name}' Statistics:\n"
                  f"{'=' * 40}\n"
                  f"Name: {self._name}\n"
                  f"Broker: {self._broker}\n"
                  f"Score Weights: {self._score_weights}\n"
                  f"Goals: {[goal.name for goal in self._goals]}\n"
                  f"Entities: {[entity.name for entity in self._entities]}\n"
                  f"{'=' * 40}")

    def init_rtmonitor(self, etopic, ltopic):
        if self._node is not None:
            self._rtmonitor = RTMonitor(self._node, etopic, ltopic)
            for goal in self._goals:
                goal.set_rtmonitor(self._rtmonitor)
        else:
            self.log_warning('Cannot initialize RTMonitor without a communication node')

    def gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')

    def _create_comm_node(self, broker, heartbeats=False):
        if broker.__class__.__name__ == 'RedisBroker':
            from commlib.transports.redis import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                db=broker.db,
                username=broker.username,
                password=broker.password,
                reconnect_attempts=0,
            )
        elif broker.__class__.__name__ == 'AMQPBroker':
            from commlib.transports.amqp import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                vhost=broker.vhost,
                username=broker.username,
                password=broker.password,
                reconnect_attempts=0,
            )
        elif broker.__class__.__name__ == 'MQTTBroker':
            from commlib.transports.mqtt import ConnectionParameters
            conn_params = ConnectionParameters(
                host=broker.host,
                port=broker.port,
                username=broker.username,
                password=broker.password,
                reconnect_attempts=0,
            )
        node = Node(
            node_name=self._name,
            connection_params=conn_params,
            heartbeats=heartbeats,
            debug=False,
        )
        return node

    def add_goal(self, goal: Goal):
        """
        Adds a goal to the list of goals.

        Args:
            goal (Goal): The goal to be added to the list.
        """
        self._goals.append(goal)

    def start_entities(self, goals: List[Goal] = None) -> None:
        """
        Starts all entities associated with the goals in the scenario.

        This method iterates over each goal in the scenario and calls the
        `start` method on each entity associated with that goal.
        """
        for goal in goals:
            if goal.__class__.__name__ == 'ComplexGoal':
                self.start_entities(goal.goals)
            elif goal.__class__.__name__ == 'MovingAreaGoal':
                if goal.motion_entity is not None:
                    goal.motion_entity.start()
                for entity in goal.entities:
                    entity.start()
            else:
                for entity in goal.entities:
                    entity.start()

    def run_seq(self) -> None:
        """
        Executes the scenario in a sequential manner.

        This method performs the following steps:
        1. Starts the entities involved in the scenario.
        2. Iterates over each goal in the scenario and triggers its entry action.
        3. Logs the completion of the scenario in ordered/sequential mode.
        4. Calculates the score for the scenario.
        5. Logs the results and the score of the scenario.

        Returns:
            None
        """
        self.print_stats()
        if self._node:
            self._node.run()
            time.sleep(0.5)
        if self._rtmonitor:
            self.send_scenario_started("sequential")
        self.start_entities(self._goals)
        for g in self._goals:
            g.enter()
        self.log_info(
            f"{'=' * 40}\n"
            f"Scenario '{self._name}' Completed (Sequential Mode)\n"
            f"{'=' * 40}\n"
            "Results:\n" +
            "\n".join([f"  - {goal_name}: {'✓' if goal_status else '✗'}" for goal_name, goal_status in self.make_result_list()]) +
            f"\n{'=' * 40}\n"
            f"Final Score: {self.calc_score():.2f}\n"
            f"{'=' * 40}"
        )
        if self._rtmonitor:
            self.send_scenario_finished("sequential")
            time.sleep(0.1)
        if self._node:
            self._node.stop()

    def run_concurrent(self) -> None:
        """
        Executes the scenario in concurrent mode using multiple threads.

        This method starts the entities, then creates a thread pool executor with a number of threads
        equal to the number of goals. Each goal's `enter` method is submitted to the executor as a task.
        The method waits for all tasks to complete, logs the completion of the scenario, calculates the
        score, and logs the results and score.

        Returns:
            None
        """
        self.print_stats()
        if self._node:
            self._node.run()
            time.sleep(0.5)
        if self._rtmonitor:
            self.send_scenario_started("concurrent")
        self.start_entities(self._goals)
        n_threads = len(self._goals)
        futures = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            future = executor.submit(goal.enter, )
            futures.append(future)
        _ = [f for f in as_completed(futures)]
        self.log_info(
            f"{'=' * 40}\n"
            f"Scenario '{self._name}' Completed (Concurrent Mode)\n"
            f"{'=' * 40}\n"
            "Results:\n" +
            "\n".join([f"  - {goal_name}: {'✓' if goal_status else '✗'}" for goal_name, goal_status in self.make_result_list()]) +
            f"\n{'=' * 40}\n"
            f"Final Score: {self.calc_score():.2f}\n"
            f"{'=' * 40}"
        )
        if self._rtmonitor:
            self.send_scenario_finished("concurrent")
            time.sleep(0.1)
        if self._node:
            self._node.stop()

    def send_scenario_started(self, execution: str):
        msg_data = {
            "name": self._name,
            "goals": [g.serialize() for g in self._goals],
            "weights": self._score_weights,
            "execution": execution
        }
        event = EventMsg(type="scenario_started", data=msg_data)
        self.log_info(f'Sending scenario started event: {event}')
        self._rtmonitor.send_event(event)

    def send_scenario_finished(self, execution: str):
        msg_data = {
            "name": self._name,
            "score": self.calc_score(),
            "results": self.make_result_list(),
            "goals": [g.serialize() for g in self._goals],
            "weights": self._score_weights,
            "execution": execution
        }
        event = EventMsg(type="scenario_finished", data=msg_data)
        self.log_info(f'Sending scenario finished event: {event}')
        self._rtmonitor.send_event(event)

    def make_result_list(self):
        res_list = [(goal.name, goal.status) for goal in self._goals]
        return res_list

    def calc_score(self):
        """
        Calculate the weighted score for the goals.

        This method calculates the score by multiplying each goal's status by its corresponding weight.
        If the score weights are not defined, it initializes them to be equal for all goals.

        Returns:
            float: The calculated weighted score.
        """
        if self._score_weights is None:
            self._score_weights = [1.0 / len(self._goals)] * len(self._goals)
        res = [goal.status * w for goal,w in zip(self._goals, self._score_weights)]
        res = sum(res)
        return res

    def log_namespace(self):
        return f"{self.__class__.__name__}:{self.name}"

    def log(self):
        return logger

    def log_info(self, msg):
        self.log().info(f"[{self.log_namespace()}] {msg}")

    def log_warning(self, msg):
        self.log().warning(f"[{self.log_namespace()}] {msg}")

    def log_error(self, msg):
        self.log().error(f"[{self.log_namespace()}] {msg}")

    def log_debug(self, msg):
        self.log().debug(f"[{self.log_namespace()}] {msg}")
