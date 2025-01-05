#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.area_goals import RectangleAreaGoal, CircularAreaGoal
from goalee.entity import Entity
from goalee.types import Point


"""_summary_
This script demonstrates how to use the `RectangleAreaGoal` and `CircularAreaGoal`
classes to create goals that check if an entity is within a rectangular or circular area.

Send the following JSON message to the `robot_1.pose` topic to simulate the robot's pose:

{
  "position": {"x": 1, "y": 0, "z": 0},
  "orientation": {"x": 0, "y": 0, "z": 0}
}

"""


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")

    RobotPose = Entity(
        name='MyRobotPose',
        etype='sensor',
        topic='robot_1.pose',
        attributes=[
            'position', 'orientation'
        ],
        source=broker
    )

    FrontSonar = Entity(
        name='front_sonar',
        etype='sensor',
        topic='sensors.sonar.front',
        attributes=[
            'range', 'hfov', 'vfov', 'header'
        ],
        source=broker
    )

    t = Scenario("Scenario_1", broker)

    g1 = RectangleAreaGoal(entities=[RobotPose, FrontSonar],
                           bottom_left_edge=Point(0.0, 0.0),
                           length_x=5.0,
                           length_y=5.0,
                           max_duration=30.0)
    g2 = CircularAreaGoal(entities=[RobotPose, FrontSonar],
                          center=Point(6.0, 6.0),
                          radius=5.0,
                          max_duration=30.0)
    t.add_goal(g1)
    t.add_goal(g2)
    t.run_seq()
