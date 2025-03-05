#!/usr/bin/env python3

from statistics import mean
from goalee import Scenario, MQTTBroker, RedisBroker
from goalee.entity_goals import EntityStateChange, EntityStateCondition

from goalee.entity import Entity

"""_summary_
This script demonstrates how to use the `EntityStateChange` and `EntityStateCondition`
classes to create goals that check if an entity's attribute has changed or meets a condition.

Send the following JSON message to the `sensors.sonar.front` topic to simulate the front sonar sensor:

{
    "range": 10,
    "hfov": 0.0,
    "vfov": 0.0,
    "header": {}
}
"""

if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")
    broker = RedisBroker(host='localhost', port=6379, username="", password="")

    FrontSonar = Entity(
        name='front_sonar',
        etype='sensor',
        topic='sensors.sonar.front',
        attributes=[
            'range', 'hfov', 'vfov', 'header'
        ],
        source=broker
    )

    scenario = Scenario("Scenario_1", broker)

    g1 = EntityStateChange(entity=FrontSonar,
                           max_duration=10.0)
    g2 = EntityStateCondition(
        entities=[FrontSonar],
        max_duration=10.0,
        condition=lambda entities: True if
            entities['front_sonar'].attributes['range'] > 5 else False
    )
    FrontSonar.init_attr_buffer("range", 10)
    g3 = EntityStateCondition(
        entities=[FrontSonar],
        max_duration=10.0,
        condition=lambda entities: True if
            mean(entities['front_sonar'].get_buffer('range', 5)) > 5 else False
    )
    scenario.add_goal(g1)
    scenario.add_goal(g2)
    scenario.add_goal(g3)
    etopic = f'monitor.{scenario.name}.event'
    ltopic = f'monitor.{scenario.name}.log'
    scenario.init_rtmonitor(etopic, ltopic)
    scenario.run_seq()
