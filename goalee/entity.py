from collections import deque
from typing import Any, List

from commlib.node import Node


# A class representing an entity communicating via an MQTT broker on a specific topic
class Entity:
    def __init__(self, name: str, etype: str, topic: str,
                 attributes: List[str, Any], source=None,
                 init_buffers: bool = False,
                 buffer_length: int = 10) -> None:
        # Entity name
        self.name = name
        self.camel_name = self.to_camel_case(name)
        self.etype = etype
        # MQTT topic for Entity
        self.topic = topic
        # Entity state
        self.state = {}
        # Set Entity's MQTT Broker
        self.source = source
        # Entity's Attributes
        self.attributes = {key: None for key in attributes}
        self.attributes_buff = {attr: None for attr in self.attributes}
        self.buffer_length = buffer_length
        if init_buffers:
            for attr in self.attributes:
                self.init_attr_buffer(attr, self.buffer_length)


    def get_buffer(self, attr_name: str, size: int = None):
        size = size if size is not None else self.attributes_buff[attr_name].maxlen
        if len(self.attributes_buff[attr_name]) != \
            self.attributes_buff[attr_name].maxlen:
            return [0] * size
        else:
            return self.attributes_buff[attr_name]

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
                password=self.source.password
            )
        else:
            raise ValueError('Invalid broker type')
        self.conn_params = conn_params

        self.node = Node(node_name=self.camel_name,
                         connection_params=self.conn_params,
                         debug=False)

    def start(self):
        # Create and start communications subscriber on Entity's topic
        self.create_node()
        self.subscriber = self.node.create_subscriber(
            topic=self.topic,
            on_message=self.update_state
        )
        self.subscriber.run()

        # Create communications publisher on Entity's topic
        self.publisher = self.node.create_publisher(
            topic=self.topic,
        )

    # Callback function for updating Entity state and triggering automations evaluation
    def update_state(self, new_state):
        """
        Function for updating Entity state. Meant to be used as a callback function by the Entity's subscriber object
        (commlib-py).
        :param new_state: Dictionary containing the Entity's state
        :return:
        """
        # Update state
        self.state = new_state
        # Update attributes based on state
        self.update_attributes(new_state)
        self.update_buffers(new_state)

    def update_buffers(self, new_state):
        """
        Recursive function used by update_state() mainly to updated
            dictionaries/objects and normal Attributes.
        """
        # Update attributes
        for attribute, value in new_state.items():
            # If value is a dictionary, also update the Dict's subattributes/items
            if self.attributes_buff[attribute] is not None:
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

