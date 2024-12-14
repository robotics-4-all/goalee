#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.area_goals import RectangleAreaGoal, CircularAreaGoal
from goalee.entity import Entity
from goalee.types import Point


RobotPose = Entity(
    name='MyRobotPose',
    etype='sensor',
    topic='myrobot.pose',
    attributes=[
        'position', 'orientation'
    ],
    # broker=broker
)


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883)

    t = Scenario("Scenario_1", broker)

    g1 = RectangleAreaGoal(entities=[RobotPose],
                           bottom_left_edge=Point(0.0, 0.0),
                           length_x=5.0,
                           length_y=5.0,
                           max_duration=30.0)
    g2 = CircularAreaGoal(entities=[RobotPose],
                          center=Point(6.0, 6.0),
                          radius=5.0,
                          max_duration=30.0)
    t.add_goal(g1)
    t.add_goal(g2)
    t.run_seq()
