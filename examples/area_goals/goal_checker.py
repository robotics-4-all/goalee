#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.area_goals import RectangleAreaGoal, CircularAreaGoal
from goalee.types import Point


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g1 = RectangleAreaGoal('robot.pose', Point(10.0, 10.0), 5.0, 5.0,
                           max_duration=10.0)
    g2 = CircularAreaGoal('robot.pose', Point(20.0, 20.0), 5.0,
                          max_duration=10.0)
    t.add_goal(g1)
    t.add_goal(g2)
    t.run_seq()
