#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g1 = TopicMessageReceivedGoal(topic='sensors.sonar.front')
    g2 = TopicMessageParamGoal(topic='sensors.sonar.front',
                               condition=lambda msg: True if msg['range'] > 5 \
                               else False)
    t.add_goal(g1)
    t.add_goal(g2)

    t.run_seq()
