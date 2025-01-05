#!/usr/bin/env python3

from goalee import Scenario, MQTTBroker
from goalee.complex_goal import ComplexGoal, ComplexGoalAlgorithm
from goalee.entity_goals import EntityStateChange, EntityStateCondition

from goalee.entity import Entity


if __name__ == '__main__':
    broker = MQTTBroker(host='localhost', port=1883, username="", password="")
    TempSensor1 = Entity(
        name='TempSensor1',
        etype='sensor',
        topic='bedroom.sensor.temperature',
        attributes=['temp'],
        source=MQTTBroker(
            host='localhost',
            port=1883,
            username='',
            password='',
        )
    )
    TempSensor2 = Entity(
        name='TempSensor2',
        etype='sensor',
        topic='bathroom.sensor.temperature',
        attributes=['temp'],
        source=MQTTBroker(
            host='localhost',
            port=1883,
            username='',
            password='',
        )
    )
    FrontSonar = Entity(
        name='FrontSonar',
        etype='sensor',
        topic='sensors.sonar.front',
        attributes=[
            'range', 'hfov', 'vfov', 'header'
        ],
        source=broker
    )
    RearSonar = Entity(
        name='RearSonar',
        etype='sensor',
        topic='sensors.sonar.front',
        attributes=[
            'range', 'hfov', 'vfov', 'header'
        ],
        source=broker
    )

    t = Scenario("Scenario_1", broker)

    g1 = EntityStateCondition(entities=[FrontSonar],
                            #   max_duration=10.0,
                              condition=lambda entities: True if
                                  entities['FrontSonar'].attributes['range'] > 5 \
                                  else False
                              )
    g2 = EntityStateCondition(entities=[RearSonar],
                            #   max_duration=10.0,
                              condition=lambda entities: True if
                                  entities['RearSonar'].attributes['range'] > 5 \
                                  else False
                              )

    cg = ComplexGoal(max_duration=5, min_duration=1,
                     algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED_ORDERED)
    # Add goals in complex goal
    cg.add_goal(g1)
    cg.add_goal(g2)

    g3 = EntityStateCondition(entities=[TempSensor1],
                            #   max_duration=10.0,
                              condition=lambda entities: True if
                                  entities['TempSensor1'].attributes['temp'] > 5 \
                                  else False
                              )
    g4 = EntityStateCondition(entities=[TempSensor2],
                            #   max_duration=10.0,
                              condition=lambda entities: True if
                                  entities['TempSensor2'].attributes['temp'] > 5 \
                                  else False
                              )
    cg2 = ComplexGoal(max_duration=5, min_duration=1,
                      algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED)
    cg2.add_goal(g3)
    cg2.add_goal(g4)

    # Add goal to target
    t.add_goal(cg)
    t.add_goal(cg2)
    # Run Target
    t.run_seq()
