#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker, RedisBroker
from goalee.trajectory_goals import WaypointTrajectoryGoal
from goalee.entity import Entity
from goalee.types import Point


"""_summary_

"""


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")
    broker = RedisBroker(host='localhost', port=6379, username="", password="")

    RobotPose = Entity(
        name='MyRobotPose',
        etype='sensor',
        topic='robot_1.pose',
        attributes=[
            'position', 'orientation'
        ],
        source=broker
    )

    g1 = WaypointTrajectoryGoal(
        name="GammaWaypoint",
        entity=RobotPose,
        waypoints=[Point(2.0, 0.0), Point(4.0, 0.0), Point(6.0, 0.0), Point(8.0, 0.0),
                   Point(8.0, 2.0), Point(8.0, 4.0), Point(8.0, 6.0), Point(8.0, 8.0)
                   ],
        deviation=0.5,
        max_duration=30.0
    )
    scenario = Scenario(
        name="Scenario_1",
        broker=broker,
        goals=[g1]
    )
    scenario.run_seq()
