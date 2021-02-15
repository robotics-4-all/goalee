#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.complex_goal import ComplexGoal
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g1 = TopicMessageReceivedGoal(topic='sensors.sonar.front')
    g2 = TopicMessageParamGoal(topic='sensors.sonar.front',
                               condition=lambda msg: True if msg['range'] > 2 \
                               else False)
    cg = ComplexGoal(max_duration=10, min_duration=0)
    # Add goals in complex goal
    cg.add_goal(g1)
    cg.add_goal(g2)
    # Add goal to target
    t.add_goal(cg)
    # Run Target
    t.run_seq()
