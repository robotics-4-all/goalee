#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.entity_goals import EntityStateChange, EntityStateCondition

from goalee.entity import Entity



if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")

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

    g1 = EntityStateChange(entity=FrontSonar,
                           max_duration=10.0)
    g2 = EntityStateCondition(entities=[FrontSonar],
                              max_duration=10.0,
                              condition=lambda entities: True if
                                  entities['front_sonar'].attributes['range'] > 5 \
                                  else False
                              )
    t.add_goal(g1)
    t.add_goal(g2)

    t.run_seq()
