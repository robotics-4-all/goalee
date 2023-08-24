#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.entity_goals import EntityStateChange, EntityStateCondition


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883)
    t = Scenario(broker)

    g1 = EntityStateChange(topic='sensors.sonar.front',
                           max_duration=10.0)
    g2 = EntityStateCondition(topic='sensors.sonar.front',
                              max_duration=10.0,
                              condition=lambda msg: True if msg['range'] > 5 \
                              else False)
    t.add_goal(g1)
    t.add_goal(g2)

    t.run_seq()
