#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader
from pydantic import Field
from commlib.node import Node


class PoseMessage(PubSubMessage):
    # header: MessageHeader = MessageHeader()
    position: dict = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})
    orientation: dict = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'mqtt'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='',
                connection_params=conn_params,
                debug=False)

    pub = node.create_publisher(msg_type=PoseMessage,
                                topic='myrobot.pose')
    node.run()

    msg = PoseMessage()
    try:
        while True:
            print(msg)
            pub.publish(msg)
            msg.position['x'] += 1
            msg.position['y'] += 1
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()
