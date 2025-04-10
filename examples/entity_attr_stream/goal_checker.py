#!/usr/bin/env python3

from statistics import mean
from goalee import Scenario, MQTTBroker, RedisBroker
from goalee.entity_goals import AttrStreamStrategy, EntityStateChange, EntityStateCondition, EntityAttrStream

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

    g1 = EntityAttrStream(
        entity=FrontSonar,
        attr='range',
        value=[2, 3, 4, 5],
        strategy=AttrStreamStrategy.ALL_ORDERED,
        max_duration=30.0,
    )
    g2 = EntityAttrStream(
        entity=FrontSonar,
        attr='range',
        value=[5, 2, 4, 3],
        strategy=AttrStreamStrategy.ALL,
        max_duration=30.0,
    )
    scenario = Scenario(
        name="Scenario_1",
        broker=broker,
        goals=[g1, g2]
    )

    etopic = f'monitor.{scenario.name}.event'
    ltopic = f'monitor.{scenario.name}.log'
    scenario.init_rtmonitor(etopic, ltopic)
    scenario.run_seq()
