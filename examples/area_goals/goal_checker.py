#!/usr/bin/env python3

from goalee import Target, RedisBroker
from goalee.area_goals import RectangleAreaGoal, CircularAreaGoal
from goalee.types import Point


if __name__ == '__main__':
    middleware = RedisBroker()
    return

    g1 = RectangleAreaGoal(topic='robot.pose',
                           bottom_left_edge=Point(0.0, 0.0),
                           length_x=5.0,
                           length_y=5.0,
                           max_duration=10.0)
    g2 = CircularAreaGoal(topic='robot.pose',
                          center=Point(10.0, 10.0),
                          radius=5.0,
                          max_duration=10.0)
    t.add_goal(g1)
    t.add_goal(g2)
    t.run_concurrent()
