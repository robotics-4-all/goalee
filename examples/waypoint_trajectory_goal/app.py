#!/usr/bin/env python

import sys
import time
from typing import Dict

from commlib.msg import PubSubMessage, MessageHeader
from pydantic import Field
from commlib.node import Node
from commlib.transports.redis import ConnectionParameters


"""_summary_
This example demonstrates how to create a simple robot that moves to a specific position.
The robot's position is published to the `robot_1.pose` topic.
"""



class PoseMessage(PubSubMessage):
    # header: MessageHeader = MessageHeader()
    position: Dict[str, float] = Field(
        default_factory=lambda: {'x': 0.0, 'y': 0.0, 'z': 0.0})
    orientation: Dict[str, float] = Field(
        default_factory=lambda: {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0})


class Robot(Node):
    def __init__(self, name, connection_params, pose_uri, velocity_linear=2,
                 velocity_angular=0.1, *args, **kwargs):
        self.name = name
        self.pose = PoseMessage()
        self.pose_uri = pose_uri
        self.velocity_linear = velocity_linear
        self.velocity_angular = velocity_angular
        super().__init__(node_name=name, connection_params=connection_params,
                         *args, **kwargs)
        self.pose_pub = self.create_publisher(msg_type=PoseMessage,
                                              topic=self.pose_uri)

    def move(self, x, y, interval=0.2):
        vel = self.velocity_linear
        current_x = self.pose.position['x']
        current_y = self.pose.position['y']

        distance = ((x - current_x)**2 + (y - current_y)**2)**0.5
        distance_x = x - current_x
        distance_y = y - current_y

        steps = int(distance / (vel * interval))
        step_distance_x = (distance_x / distance) * vel * interval
        step_distance_y = (distance_y / distance) * vel * interval

        for _ in range(steps):
            current_x += step_distance_x
            current_y += step_distance_y
            self.publish_position(current_x, current_y)
            print(f'Current position: x={current_x:.2f}, y={current_y:.2f}')
            time.sleep(interval)

        # Ensure final position is exactly the target position
        self.publish_position(x, y)
        print(f'Final position: x={x:.2f}, y={y:.2f}')

    def turn(self, angle, interval=0.2):
        vel = self.velocity_angular
        current_yaw = self.pose.orientation['yaw']
        target_yaw = angle
        direction = 1 if target_yaw > current_yaw else -1

        distance = abs(target_yaw - current_yaw)
        steps = int(distance / (vel * interval))
        step_distance_yaw = direction * vel * interval

        for _ in range(steps):
            current_yaw += step_distance_yaw
            self.publish_orientation(current_yaw)
            print(f'Current orientation: yaw={current_yaw:.2f}')
            time.sleep(interval)

        # Ensure final orientation is exactly the target angle
        self.publish_orientation(target_yaw)
        print(f'Final orientation: yaw={target_yaw:.2f}')

    def publish_orientation(self, yaw):
        self.pose.orientation['yaw'] = yaw
        self.pose_pub.publish(self.pose)

    def publish_position(self, x, y):
        self.pose.position['x'] = x
        self.pose.position['y'] = y
        self.pose_pub.publish(self.pose)

    def publish_pose(self, x, y, yaw=0):
        self.pose.position['x'] = x
        self.pose.position['y'] = y
        self.pose.orientation['yaw'] = yaw
        self.pose_pub.publish(self.pose)


if __name__ == '__main__':
    conn_params = ConnectionParameters()

    robot_1 = Robot(name='robot_1', connection_params=conn_params,
                    pose_uri='robot_1.pose', heartbeats=False)

    try:
        robot_1.run()
        robot_1.move(2, 0)
        robot_1.move(4, 0)
        robot_1.move(6, 0)
        robot_1.move(8, 0)
        robot_1.move(8, 2)
        robot_1.move(8, 4)
        robot_1.move(8, 6)
        robot_1.move(8, 8)
        robot_1.stop()
    except KeyboardInterrupt:
        robot_1.stop()
