#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader
from commlib.node import Node, TransportType


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


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

    node = Node(node_name='sensors.sonar.front',
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    pub = node.create_publisher(msg_type=SonarMessage,
                                topic='sensors.sonar.front')

    msg = SonarMessage()
    while True:
        print(f'Sending Message: {msg}')
        pub.publish(msg)
        msg.range += 1
        time.sleep(1)
