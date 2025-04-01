import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Optional

from commlib.node import Node
from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.brokers import Broker
from goalee.logging import default_logger as logger
from goalee.rtmonitor import RTMonitor, EventMsg


class Scenario:
    def __init__(self,
                 name: str = "",
                 broker: Optional[Broker] = None,
                 goal_weights: Optional[List] = None,
                 antigoal_weights: Optional[List] = None,
                 goals: Optional[List[Goal]] = [],
                 anti_goals: Optional[List[Goal]] = [],
                 fatal_goals: Optional[List[Goal]] = [],
                 goal_tick_freq_hz: int = None):
        self._broker: Broker = broker
        self._rtmonitor: RTMonitor = None
        if name in (None, "") or len(name) == 0:
            name = self.gen_random_name()
        self._name: str = name
        self._goal_weights: List[float] = goal_weights
        self._antigoal_weights: List[float] = antigoal_weights
        if self._broker is not None:
            self._node = self._create_comm_node(self._broker)
        else:
            self._node: Node = None
        self._goals: List[Goal] = goals
        self._anti_goals: List[Goal] = anti_goals
        self._fatal_goals: List[Goal] = fatal_goals
        self._entities: List[Entity] = []
        self._start_ts = self.get_current_ts()
        self._goal_tick_freq_hz = goal_tick_freq_hz or int(os.getenv("GOAL_TICK_FREQ_HZ", "100"))

        n_threads = len(self._fatal_goals + self._goals + self._anti_goals) + 1
        self._thread_executor = ThreadPoolExecutor(n_threads)

        if self._goal_weights is None:
            self._goal_weights = [1.0 / len(self._goals)] * len(self._goals)
        elif len(self._goal_weights) != len(self._goals):
            self.log_warning("Goal weights length does not match the number of goals. Initializing to equal weights.")
            self._goal_weights = [1.0 / len(self._goals)] * len(self._goals)
        if self._antigoal_weights is None:
            if len(self._anti_goals) > 0:
                self._antigoal_weights = [1.0 / len(self._anti_goals)] * len(self._anti_goals)
        elif len(self._antigoal_weights) != len(self._anti_goals):
            self.log_warning("Anti-goal weights length does not match the number of anti-goals. Initializing to equal weights.")
            self._antigoal_weights = [1.0 / len(self._anti_goals)] * len(self._anti_goals)

        for goal in self._goals:
            goal.set_tick_freq(self._goal_tick_freq_hz)
        for goal in self._anti_goals:
            goal.set_tick_freq(self._goal_tick_freq_hz)
        for goal in self._fatal_goals:
            goal.set_tick_freq(self._goal_tick_freq_hz)

    @property
    def name(self):
        return self._name

    def build_entity_list(self):
        self._entities = []  # Clear previous entities
        for goal in self._goals:
            for entity in goal.entities:
                if entity not in self._entities:
                    self._entities.append(entity)

    def print_stats(self):
        self.log_info(f"Scenario '{self._name}' Configuration:\n"
                  f"{'=' * 80}\n"
                  f"    Name: {self._name}\n"
                  f"    Broker: {self._broker}\n"
                  f"    Entities: {[entity.name for entity in self._entities]}\n"
                  f"    Goals: {[goal.name for goal in self._goals]}\n"
                  f"    Anti-Goals: {[goal.name for goal in self._anti_goals]}\n"
                  f"    Fatal-Goals: {[goal.name for goal in self._fatal_goals]}\n"
                  f"    Goal Weights: {self._goal_weights}\n"
                  f"    Anti-Goal Weights: {self._antigoal_weights}\n"
                  f"{'=' * 80}")

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
            elif goal.__class__.__name__ == 'GoalRepeater':
                self.start_entities([goal._goal])
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
        self.build_entity_list()
        self.print_stats()
        if self._node:
            self._node.run()
            time.sleep(0.5)
        if self._rtmonitor:
            self.send_scenario_started("sequential")

        self.start_entities(self._goals + self._anti_goals + self._fatal_goals)

        self.start_fatal_goals()
        self.start_antigoals()

        for g in self._goals:
            g.enter()
            self.send_scenario_update("sequential")
            _break = False
            for f in self._fatal_goals:
                if f.state in (GoalState.TERMINATED, GoalState.COMPLETED):
                    _break = True
                    break
            if _break:
                break
        self.print_results()

        if self._rtmonitor:
            self.send_scenario_finished("sequential")

        self.terminate_fatal_goals()
        self.terminate_all_goals()
        self.stop_thread_executor()

        if self._node:
            time.sleep(0.5)
            self._node.stop()

    def run_concurrent(self) -> None:
        """
        Executes the scenario in concurrent mode using multiple threads.

        This method starts the entities, then creates a thread pool executor with a number of threads
        equal to the number of goals. Each goal's `enter` method is submitted to the executor as a task.
        The method waits for all tasks to complete, logs the completion of the scenario, calculates the
        score, and logs the results and score.

        """
        self.build_entity_list()
        self.print_stats()
        if self._node:
            self._node.run()
            time.sleep(0.5)

        if self._rtmonitor:
            self.send_scenario_started("concurrent")

        self.start_entities(self._goals + self._anti_goals + self._fatal_goals)

        self.start_fatal_goals()
        self.start_antigoals()

        futures = []
        for goal in self._goals:
            future = self._thread_executor.submit(goal.enter, )
            futures.append(future)
        for f in as_completed(futures):
            try:
                f.result()
                self.send_scenario_update("concurrent")
            except Exception as e:
                self.log_error(f"Error in goal execution: {e}")

        self.print_results()

        if self._rtmonitor:
            self.send_scenario_finished("concurrent")

        self.terminate_fatal_goals()
        self.terminate_all_goals()
        self.stop_thread_executor()

        if self._node:
            time.sleep(0.5)
            self._node.stop()

    def start_goals(self):
        futures = []
        for goal in self._goals:
            future = self._thread_executor.submit(goal.enter, )
            futures.append(future)
        for future in futures:
            future.add_done_callback(self.on_goal)

    def start_fatal_goals(self):
        futures = []
        for goal in self._fatal_goals:
            future = self._thread_executor.submit(goal.enter, )
            futures.append(future)
        for future in futures:
            future.add_done_callback(self.on_fatal)

    def start_antigoals(self):
        futures = []
        for goal in self._anti_goals:
            future = self._thread_executor.submit(goal.enter, )
            futures.append(future)
        for future in futures:
            future.add_done_callback(self.on_antigoal)

    def terminate_fatal_goals(self):
        for goal in self._fatal_goals:
            if goal.state not in (GoalState.COMPLETED, GoalState.FAILED, GoalState.TERMINATED):
                goal.terminate()

    def terminate_all_goals(self):
        for goal in self._goals + self._anti_goals:
            if goal.state not in (GoalState.COMPLETED, GoalState.FAILED, GoalState.TERMINATED):
                goal.terminate()

    def on_fatal(self, f):
        self.log_error(f"Fatal Goal <{f.result().name}> exited with state: {f.result().state}")
        self.terminate_all_goals()

    def on_goal(self, f):
        self.log_info(f"Goal <{f.result().name}> exited with state: {f.result().state}")

    def on_antigoal(self, f):
        self.log_info(f"AntiGoal <{f.result().name}> exited with state: {f.result().state}")

    def stop_thread_executor(self, wait: bool = False, force: bool = True):
        try:
            self._thread_executor.shutdown(wait=wait, cancel_futures=force)
        except Exception:
            pass

    def print_results(self):
        self.log_info(
            f"Scenario '{self._name}' Completed (Concurrent Mode)\n"
            f"{'=' * 80}\n"
            "Results:\n" +
            "   Goals:\n" +
            "\n".join([f"       - {goal_name}: {'✓' if goal_status else '✗'}" for
                       goal_name, goal_status in [(goal.name, goal.status) for goal in self._goals]]) +
            "\n   Anti-Goals:\n" +
            "\n".join([f"       - {goal_name}: {'✓' if goal_status else '✗'}" for
                       goal_name, goal_status in [(goal.name, goal.status) for goal in self._anti_goals]]) +
            "\n   Fatal Goals:\n" +
            "\n".join([f"       - {goal_name}: {'✓' if goal_status else '✗'}" for
                       goal_name, goal_status in [(goal.name, goal.status) for goal in self._fatal_goals]]) +
            f"\n{'=' * 80}\n"
            f"Final Score (goals - antigoals): {self.calc_score():.2f}\n"
            f"{'=' * 80}"
        )

    def send_scenario_started(self, execution: str):
        if self._rtmonitor is None:
            return
        msg_data = {
            "name": self._name,
            "goals": [g.serialize() for g in self._goals],
            "anti_goals": [g.serialize() for g in self._anti_goals],
            "fatal_goals": [g.serialize() for g in self._fatal_goals],
            "goal_weights": self._goal_weights,
            "antigoal_weights": self._antigoal_weights,
            "execution": execution,
            "timestamp": self.get_current_ts(),
            "elapsed_time": self.get_current_ts() - self._start_ts
        }
        event = EventMsg(type="scenario_started", data=msg_data)
        self.log_info(f'Sending scenario started event: {event}')
        self._rtmonitor.send_event(event)

    def send_scenario_update(self, execution: str):
        if self._rtmonitor is None:
            return
        msg_data = {
            "name": self._name,
            "goals": [g.serialize() for g in self._goals],
            "anti_goals": [g.serialize() for g in self._anti_goals],
            "fatal_goals": [g.serialize() for g in self._fatal_goals],
            "score": self.calc_score(),
            "goal_weights": self._goal_weights,
            "antigoal_weights": self._antigoal_weights,
            "execution": execution,
            "timestamp": self.get_current_ts(),
            "elapsed_time": self.get_current_ts() - self._start_ts
        }
        event = EventMsg(type="scenario_update", data=msg_data)
        self.log_info(f'Sending scenario update event: {event}')
        self._rtmonitor.send_event(event)

    def send_scenario_finished(self, execution: str):
        if self._rtmonitor is None:
            return
        msg_data = {
            "name": self._name,
            "score": self.calc_score(),
            "results": self.make_result_list(),
            "goals": [g.serialize() for g in self._goals],
            "anti_goals": [g.serialize() for g in self._anti_goals],
            "fatal_goals": [g.serialize() for g in self._fatal_goals],
            "goal_weights": self._goal_weights,
            "antigoal_weights": self._antigoal_weights,
            "execution": execution,
            "timestamp": self.get_current_ts(),
            "elapsed_time": self.get_current_ts() - self._start_ts
        }
        event = EventMsg(type="scenario_finished", data=msg_data)
        self.log_info(f'Sending scenario finished event: {event}')
        self._rtmonitor.send_event(event)

    def make_result_list(self):
        res_list = [(goal.name, goal.status) for goal in self._goals]
        return res_list


    @staticmethod
    def get_current_ts():
        """
        Get the current timestamp with nanosecond accuracy as an integer.

        Returns:
            int: The current timestamp in nanoseconds.
        """
        return int(time.perf_counter_ns() * 1e-6)

    def calc_score(self):
        """
        Calculate the weighted score for the goals.

        This method calculates the score by multiplying each goal's status by its corresponding weight.
        If the score weights are not defined, it initializes them to be equal for all goals.

        Returns:
            float: The calculated weighted score.
        """
        goal_res = [goal.status * w for goal,w in zip(self._goals, self._goal_weights)] if \
            len(self._goals) > 0 else [0]
        antigoal_res = [goal.status * w for goal,w in zip(self._anti_goals, self._antigoal_weights)] if \
            len(self._anti_goals) > 0 else [0]
        res = sum(goal_res) - sum(antigoal_res)
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
