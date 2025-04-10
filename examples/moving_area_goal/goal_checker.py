#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.area_goals import AreaGoalTag, MovingAreaGoal
from goalee.entity import Entity


"""_summary_
This script demonstrates how to use the `RectangleAreaGoal` and `CircularAreaGoal`
classes to create goals that check if an entity is within a rectangular or circular area.

Send the following JSON message to the `robot_1.pose` and `robot_2.pose` topics to simulate the robot's pose:

{
  "position": {"x": 0, "y": 0, "z": 0},
  "orientation": {"x": 0, "y": 0, "z": 0}
}

"""


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")

    Robot1Pose = Entity(
        name='MyRobot1Pose',
        etype='sensor',
        topic='robot_1.pose',
        attributes=[
            'position', 'orientation'
        ],
        source=broker
    )

    Robot2Pose = Entity(
        name='MyRobot2Pose',
        etype='sensor',
        topic='robot_2.pose',
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

    g1 = MovingAreaGoal(motion_entity=Robot1Pose,
                        entities=[Robot2Pose],
                        radius=2.0,
                        max_duration=10.0,
                        tag=AreaGoalTag.AVOID)

    t = Scenario(
        name="Scenario_1",
        broker=broker,
        goals=[g1]
    )
    etopic = f'monitor.{t.name}.event'
    ltopic = f'monitor.{t.name}.log'
    t.init_rtmonitor(etopic, ltopic)
    t.run_seq()
