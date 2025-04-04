from collections import deque
from typing import Any, Dict, List

from commlib.node import Node
from goalee.logging import default_logger as logger


# A class representing an entity communicating via an MQTT broker on a specific topic
class Entity:
    def __init__(self, name: str,
                 etype: str,
                 topic: str,
                 attributes: List[str],
                 source=None,
                 init_buffers: bool = False,
                 buffer_length: int = 10,
                 strict_mode: bool = False) -> None:
        # Entity name
        self.name = name
        self.camel_name = self.to_camel_case(name)
        self.etype = etype
        # MQTT topic for Entity
        self.topic = topic
        self._strict = strict_mode
        # Entity state
        self.state = None
        # Set Entity's MQTT Broker
        self.source = source
        # Entity's Attributes
        self.attributes = {key: None for key in attributes}
        self.attributes_buff = {attr: None for attr in self.attributes}
        self.buffer_length = buffer_length
        if init_buffers:
            for attr in self.attributes:
                self.init_attr_buffer(attr, self.buffer_length)
        self._initialized = False
        self._started = False

    @property
    def initialized(self):
        return self._initialized

    def __getitem__(self, key):
        # Allow dictionary-style access to attributes
        # return getattr(self, key)
        return self.attributes[key]

    def get_buffer(self, attr_name: str, size: int = None):
        size = size if size is not None else self.attributes_buff[attr_name].maxlen
        if len(self.attributes_buff[attr_name]) != \
            self.attributes_buff[attr_name].maxlen:
            buffer = [0] * size
        else:
            buffer = list(self.attributes_buff[attr_name])[-size:]
        return buffer

    def get_attr(self, attr_name: str) -> Any:
        return self.attributes[attr_name]

    def init_attr_buffer(self, attr_name, size):
        self.attributes_buff[attr_name] = deque(maxlen=size)
        # self.attributes_buff[attr_name].extend([0] * size)

    def to_camel_case(self, snake_str):
        return "".join(x.capitalize() for x in snake_str.lower().split("_"))

    def create_node(self):
        if self.source is None:
            raise ValueError(f'Entity {self.name} not assigned a broker')
        if self.source.__class__.__name__ == 'RedisBroker':
            from commlib.transports.redis import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.source.host,
                port=self.source.port,
                db=self.source.db,
                username=self.source.username,
                password=self.source.password
            )
        elif self.source.__class__.__name__ == 'AMQPBroker':
            from commlib.transports.amqp import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.source.host,
                port=self.source.port,
                vhost=self.source.vhost,
                username=self.source.username,
                password=self.source.password
            )
        elif self.source.__class__.__name__ == 'MQTTBroker':
            from commlib.transports.mqtt import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.source.host,
                port=self.source.port,
                username=self.source.username,
                password=self.source.password,
            )
        else:
            raise ValueError('Invalid broker type')
        self.conn_params = conn_params

        self.node = Node(node_name=self.camel_name,
                         connection_params=self.conn_params,
                         debug=False, heartbeats=False)
        self.subscriber = self.node.create_subscriber(
            topic=self.topic,
            on_message=self.update_state
        )

    def start(self):
        """
        Starts the entity by creating a node, setting up a subscriber to listen to messages on the entity's topic,
        and running the subscriber. Additionally, it creates a publisher for communications on the same topic.

        The subscriber will call the `update_state` method whenever a message is received on the topic.
        """
        if self._started:
            return
        self._started = True
        self.create_node()
        self.node.run()
        logger.debug(f"Started Entity <{self.name}> listening on topic <{self.topic}>")

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """
        Function for updating Entity state. Meant to be used as a callback function by the Entity's subscriber object
        (commlib-py).
        :param new_state: Dictionary containing the Entity's state
        :return:
        """
        # Update state
        # logger.info(f'[Entity {self.name}] State Change')
        state = new_state.copy()
        for key in state:
            if key not in self.attributes:
                # logger.warning(
                #     f"Entity <{self.name}> state - Message KeyError <{key}>\n"
                # )
                if self._strict:
                    logger.warning(f"Entity <{self.name}> in strict mode - Dropping invalid message")
                    return
                else:
                    continue
        self._initialized = True
        self.state = state
        # Update attributes based on state
        self.update_attributes(state)
        self.update_buffers(state)

    def update_buffers(self, new_state):
        """
        Recursive function used by update_state() mainly to updated
            dictionaries/objects and normal Attributes.
        """
        # Update attributes
        state = new_state.copy()
        for key in state:
            if self._strict and key not in self.attributes:
                logger.warning(f"Entity <{self.name}> in strict mode - Dropping invalid message")
                return
        for attribute, value in state.items():
            # If value is a dictionary, also update the Dict's subattributes/items
            if attribute in self.attributes and self.attributes_buff[attribute] is not None:
                self.attributes_buff[attribute].append(value)

    def update_attributes(self, new_state):
        """
        Recursive function used by update_state() mainly to updated
            dictionaries/objects and normal Attributes.
        """
        # Update attributes
        for key, value in new_state.items():
            # If value is a dictionary, also update the Dict's subattributes/items
            # if root[attribute].__class__.__name__ == 'TimeAttribute':
            #     setattr(root[attribute].value, 'hour', value['hour'])
            #     setattr(root[attribute].value, 'minute', value['minute'])
            #     setattr(root[attribute].value, 'second', value['second'])
            if key in self.attributes:
                self.attributes[key] = value

