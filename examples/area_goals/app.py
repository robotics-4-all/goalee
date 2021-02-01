#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass, DataField
from commlib.node import Node, TransportType


@DataClass
class PoseMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    position: dict = DataField(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='',
                transport_type=transport,
                transport_connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=False)

    pub = node.create_publisher(msg_type=PoseMessage,
                                topic='robot.pose')

    msg = PoseMessage()
    while True:
        print(msg)
        pub.publish(msg)
        msg.position['x'] += 1
        msg.position['y'] += 1
        time.sleep(1)
