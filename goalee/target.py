from abc import ABCMeta, abstractmethod
from enum import IntEnum
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from commlib.node import Node, TransportType
from goalee.goal import Goal


class MiddlewareType:
    AMQP = 0
    MQTT = 1
    REDIS = 2


class Middleware(metaclass=ABCMeta):
    host: str = None
    port: int = None
    username: str = None
    password: str = None


class AMQPMiddleware(Middleware):
    vhost: str = None

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 5672,
                 vhost: str = '/',
                 username: str = 'guest',
                 password: str = 'guest'):
        self.host = host
        self.port = port
        self.vhost = vhost
        self.username = username
        self.password = password


class RedisMiddleware(Middleware):
    db: str = None

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 username: str = '',
                 password: str = ''):
        self.host = host
        self.port = port
        self.db = db
        self.username = username
        self.password = password


class MQTTMiddleware(Middleware):
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 1883,
                 username: str = '',
                 password: str = ''):
        self.host = host
        self.port = port
        self.username = username
        self.password = password


class Target:
    def __init__(self,
                 input_middleware: Middleware,
                 output_middleware: Middleware = None,
                 name: str = None):
        self._input_middleware = input_middleware
        if name is None or len(name) == 0:
            name = self.gen_random_name()
        self._name = name
        self._input_node = self._create_comm_node(self._input_middleware)
        self._goals = []

    def gen_random_name(self) -> str:
        """gen_random_id.
        Generates a random unique id, using the uuid library.

        Args:

        Returns:
            str: String representation of the random unique id
        """
        return str(uuid.uuid4()).replace('-', '')

    def _create_comm_node(self, middleware):
        if middleware.__class__.__name__ == 'RedisMiddleware':
            from commlib.transports.redis import (ConnectionParameters,
                                                  Credentials)
            conn_params = ConnectionParameters(
                host=middleware.host,
                port=middleware.port,
                db=middleware.db,
                creds=Credentials(middleware.username,
                                  middleware.password)
            )
            transport = TransportType.REDIS
        elif middleware.__class__.__name__ == 'AMQPMiddleware':
            from commlib.transports.amqp import (ConnectionParameters,
                                                 Credentials)
            conn_params = ConnectionParameters(
                host=middleware.host,
                port=middleware.port,
                vhost=middleware.vhost,
                creds=Credentials(middleware.username,
                                  middleware.password)
            )
            transport = TransportType.AMQP
        elif middleware.__class__.__name__ == 'MQTTMiddleware':
            from commlib.transports.redis import (ConnectionParameters,
                                                  Credentials)
            conn_params = ConnectionParameters(
                host=middleware.host,
                port=middleware.port,
                creds=Credentials(middleware.username,
                                  middleware.password)
            )
            transport = TransportType.MQTT
        node = Node(node_name=self._name,
                    transport_type=transport,
                    transport_connection_params=conn_params,
                    debug=True)
        return node

    def add_goal(self, goal: Goal):
        goal.set_comm_node(self._input_node)
        self._goals.append(goal)

    def run_seq(self):
        for g in self._goals:
            g.enter()
        print(
            f'[*] - Finished Target in Ordered/Sequential Mode ({self._name})')

    def run_concurrent(self):
        n_threads = len(self._goals)
        features = []
        executor = ThreadPoolExecutor(n_threads)
        for goal in self._goals:
            feature = executor.submit(goal.enter, )
            features.append(feature)
        for f in as_completed(features):
            pass
        print(f'[*] - Finished Target in Concurrent Mode ({self._name})')
