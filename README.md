# goalee

Goalee is a Python 3.9+ library that implements goal-driven runtime verification for Cyber-Physical Systems. Part of the [GoalDSL](https://github.com/robotics-4-all/goal-dsl) ecosystem, it is used by the code generator to produce source code from a given GoalDSL model. Goalee can also be used as a standalone Python library.

## Installation

Install from PyPI:

```bash
pip install goalee
```

Or install from source:

```bash
git clone https://github.com/robotics-4-all/goalee
cd goalee
pip install .
```

For development:

```bash
pip install -e ".[dev,test]"
```

## Quick Start

The following example defines two goals that monitor entity state via a Redis broker:

```python
from goalee import Scenario, RedisBroker, Entity
from goalee.entity_goals import EntityStateCondition

broker = RedisBroker(host="localhost", port=6379)

front_sonar = Entity(
    name="FrontSonar",
    etype="sensor",
    topic="sensors.sonar.front",
    attributes=["range", "hfov", "vfov"],
    source=broker,
)

g1 = EntityStateCondition(
    name="sonar_range_check",
    entities=[front_sonar],
    condition=lambda entities: entities["FrontSonar"]["range"] > 5,
    max_duration=10.0,
)

scenario = Scenario(name="my_scenario", broker=broker, goals=[g1])
scenario.run_seq()
```

Goals are evaluated by subscribing to entity data via pub/sub messaging (Redis, MQTT, or AMQP). Scenarios can be executed in **Sequential** (`run_seq()`) or **Concurrent** (`run_concurrent()`) mode.

## Goal Types

- **EntityStateChange** / **EntityStateCondition** / **EntityAttrStream** — entity data monitoring
- **RectangleAreaGoal** / **CircularAreaGoal** / **MovingAreaGoal** — spatial/geometric checks
- **PoseGoal** / **PositionGoal** / **OrientationGoal** — pose verification
- **WaypointTrajectoryGoal** — waypoint trajectory tracking
- **ComplexGoal** — composite goals with algorithms (ALL, NONE, AT_LEAST_ONE, EXACTLY_X)
- **GoalRepeater** — run any goal N times

## Examples

Several examples can be found in the [examples/](./examples/) directory.

## License

MIT
