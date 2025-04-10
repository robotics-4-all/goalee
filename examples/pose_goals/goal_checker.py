#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.pose_goals import PositionGoal, OrientationGoal, PoseGoal
from goalee.entity import Entity
from goalee.types import Orientation, Point


"""_summary_

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

    t = Scenario("Scenario_1", broker)

    g1 = PositionGoal(
        entity=RobotPose,
        position=Point(5.0, 0.0),
        deviation=0.5,
        max_duration=30.0
    )
    g2 = PositionGoal(
        entity=RobotPose,
        position=Point(5.0, 5.0),
        deviation=0.5,
        max_duration=30.0
    )
    g3 = OrientationGoal(
        entity=RobotPose,
        orientation=Orientation(yaw=0.5),
        deviation=0.02,
        max_duration=30.0
    )
    g4 = PoseGoal(
        entity=RobotPose,
        position=Point(5.0, 5.0),
        orientation=Orientation(yaw=0.5),
        deviation_pos=0.02,
        deviation_ori=0.5,
        max_duration=30.0
    )
    t.add_goal(g1)
    t.add_goal(g2)
    t.add_goal(g3)
    t.add_goal(g4)
    t.run_seq()
