#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.goal import TopicMessageReceivedGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g1 = TopicMessageReceivedGoal(topic='sensors.sonar.front')
    g2 = TopicMessageReceivedGoal(topic='sensors.sonar.front')
    t.add_goal(g1)
    t.add_goal(g2)

    t.run_seq()
