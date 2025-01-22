#!/usr/bin/env python3

import os
from statistics import stdev as std, mean as mean, variance as var

from goalee import Scenario, RedisBroker, MQTTBroker, AMQPBroker
from goalee.entity import Entity
from goalee.area_goals import *
from goalee.complex_goal import *
from goalee.types import Point
from goalee.entity_goals import (
    EntityStateChange,
    EntityStateCondition
)

entities_list = []

TempSensor1 = Entity(
    name='TempSensor1',
    etype='sensor',
    topic='streamsim.6530f9263773c5f7858b6b33.world.world.sensor.env.temperature.sn_temperature_1.data',
    attributes=['temperature'],
    source=RedisBroker(
        host='localhost',
        port=6379,
        db=0,  # default DB number is 0
        username='',
        password='',
    )
)
entities_list.append(TempSensor1)


if __name__ == '__main__':
    broker = RedisBroker(
        host='localhost',
        port=6379,
        db=0,  # default DB number is 0
        username='',
        password='',
    )

    scenario = Scenario(
        name='MyScenario',
        broker=broker,
        score_weights=[0.5]
    )

    g = EntityStateCondition(
        name='Goal_1',
        entities=[TempSensor1],
        # condition='entities["TempSensor1"].attributes["temperature"] > 50',
        condition=lambda entities: True if entities["TempSensor1"].attributes["temperature"] > 50 else False,
        max_duration=None,
        min_duration=None,
    )
    scenario.add_goal(g)

    try:
        etopic = 'goaldsl.{U_ID}.event'.format(**{k: os.environ.get(k, "") for k in os.environ}).replace('..', '.')
        ltopic = 'goaldsl.{U_ID}.log'.format(**{k: os.environ.get(k, "") for k in os.environ}).replace('..', '.')
    except KeyError as e:
        print(f"Error occurred while retrieving environment variables: {e}")
        exit(1)
    scenario.init_rtmonitor(etopic, ltopic)

    scenario.run_concurrent()
