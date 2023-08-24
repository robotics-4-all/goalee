from collections import deque

from commlib.node import Node


# A class representing an entity communicating via an MQTT broker on a specific topic
class Entity:
    def __init__(self, name, etype, topic, attributes, broker=None):
        # Entity name
        self.name = name
        self.camel_name = self.to_camel_case(name)
        self.etype = etype
        # MQTT topic for Entity
        self.topic = topic
        # Entity state
        self.state = {}
        # Set Entity's MQTT Broker
        self.broker = broker
        # Entity's Attributes
        self.attributes = {key: None for key in attributes}
        self.attributes_buff = {attr: None for attr in self.attributes}


    def get_buffer(self, attr_name):
        if len(self.attributes_buff[attr_name]) != \
            self.attributes_buff[attr_name].maxlen:
            return [0] * self.attributes_buff[attr_name].maxlen
        else:
            return self.attributes_buff[attr_name]

    def init_attr_buffer(self, attr_name, size):
        self.attributes_buff[attr_name] = deque(maxlen=size)
        # self.attributes_buff[attr_name].extend([0] * size)

    def to_camel_case(self, snake_str):
        return "".join(x.capitalize() for x in snake_str.lower().split("_"))


    def create_node(self):
        if self.broker.__class__.__name__ == 'RedisBroker':
            from commlib.transports.redis import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.broker.host,
                port=self.broker.port,
                db=self.broker.db,
                username=self.broker.username,
                password=self.broker.password
            )
        elif self.broker.__class__.__name__ == 'AMQPBroker':
            from commlib.transports.amqp import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.broker.host,
                port=self.broker.port,
                vhost=self.broker.vhost,
                username=self.broker.username,
                password=self.broker.password
            )
        elif self.broker.__class__.__name__ == 'MQTTBroker':
            from commlib.transports.mqtt import ConnectionParameters
            conn_params = ConnectionParameters(
                host=self.broker.host,
                port=self.broker.port,
                username=self.broker.username,
                password=self.broker.password
            )
        else:
            raise ValueError('SKATA')
        self.conn_params = conn_params

        self.node = Node(node_name=self.camel_name,
                         connection_params=self.conn_params,
                         # heartbeat_uri='nodes.add_two_ints.heartbeat',
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
        self.update_attributes(self.attributes, new_state)
        self.update_buffers(self.attributes_buff, new_state)

    @staticmethod
    def update_buffers(root, new_state):
        """
        Recursive function used by update_state() mainly to updated
            dictionaries/objects and normal Attributes.
        """
        # Update attributes
        for attribute, value in new_state.items():

            # If value is a dictionary, also update the Dict's subattributes/items
            if root[attribute] is not None:
                root[attribute].append(value)

    @staticmethod
    def update_attributes(root, new_state):
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
            root[key] = value

