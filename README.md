# goalee

![CI](https://github.com/robotics-4-all/goalee/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/pypi/pyversions/goalee)
![PyPI](https://img.shields.io/pypi/v/goalee)
![License](https://img.shields.io/github/license/robotics-4-all/goalee)

Goalee is a Python 3.9+ library for goal-driven runtime verification of Cyber-Physical Systems. It lets you define goals that monitor entity state over pub/sub messaging (Redis, MQTT, or AMQP), evaluate conditions against incoming data, and orchestrate verification scenarios that run sequentially or concurrently. Part of the [GoalDSL](https://github.com/robotics-4-all/goal-dsl) ecosystem, goalee serves as the runtime target for generated code, but works just as well as a standalone library.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Goal Types](#goal-types)
- [Broker Configuration](#broker-configuration)
- [Scenario Execution](#scenario-execution)
- [Goal Lifecycle](#goal-lifecycle)
- [Configuration](#configuration)
- [Examples](#examples)
- [Development](#development)
- [Testing](#testing)
- [GoalDSL Ecosystem](#goaldsl-ecosystem)
- [License](#license)

## Features

- Define verification goals over entity state received via pub/sub messaging
- Support for Redis, MQTT, and AMQP brokers through commlib-py
- Entity-level state tracking with attribute buffers and strict mode
- Spatial and geometric goals: rectangular areas, circular areas, moving areas
- Pose verification: position, orientation, and combined pose goals
- Waypoint trajectory tracking with configurable deviation tolerance
- Composite goals with six composition algorithms (ALL, NONE, AT_LEAST_ONE, EXACTLY_X, and ordered variants)
- Goal repetition via GoalRepeater
- Anti-goals and fatal goals for negative condition monitoring
- Sequential and concurrent scenario execution with weighted scoring
- Configurable tick frequency, timeouts, minimum durations, and hold-time constraints
- Real-time monitoring with event and log publishing

## Installation

Install from PyPI:

```bash
pip install goalee
```

Install from source:

```bash
git clone https://github.com/robotics-4-all/goalee
cd goalee
pip install .
```

Install for development:

```bash
pip install -e ".[dev,test]"
```

## Quick Start

This example creates a sensor entity, defines a condition-based goal, and runs it inside a scenario:

```python
from goalee import Scenario, RedisBroker, Entity
from goalee.entity_goals import EntityStateCondition

# Configure the broker
broker = RedisBroker(host="localhost", port=6379)

# Define an entity that subscribes to sensor data
front_sonar = Entity(
    name="FrontSonar",
    etype="sensor",
    topic="sensors.sonar.front",
    attributes=["range", "hfov", "vfov"],
    source=broker,
)

# Define a goal: sonar range must exceed 5
goal = EntityStateCondition(
    name="sonar_range_check",
    entities=[front_sonar],
    condition=lambda entities: entities["FrontSonar"]["range"] > 5,
    max_duration=10.0,
)

# Create and run the scenario
scenario = Scenario(name="my_scenario", broker=broker, goals=[goal])
scenario.run_seq()
```

The scenario starts the entity's subscriber, evaluates the goal by polling the condition at a configurable tick rate, and reports results with a weighted score.

## Core Concepts

**Broker** defines the messaging transport. Goalee supports three broker types, all built as pydantic models: `RedisBroker`, `MQTTBroker`, and `AMQPBroker`. The broker is passed to entities and scenarios to configure their underlying commlib-py connections.

**Entity** represents a data source in your system. Each entity subscribes to a broker topic and receives state updates as dictionaries. Attributes are declared up front, and incoming messages update them automatically. Entities can optionally maintain attribute buffers (fixed-size deques) for time-series analysis.

**Goal** is the core verification primitive. A goal monitors one or more entities, evaluates a condition on each tick, and transitions through a state machine (IDLE, RUNNING, COMPLETED, FAILED, TERMINATED). Goals support timing constraints: `max_duration` (timeout), `min_duration` (minimum run time), and `for_duration` (condition must hold continuously for a given period).

**Scenario** orchestrates goal execution. It starts entities, runs goals either sequentially or concurrently, handles anti-goals and fatal goals, and computes a weighted score from the results.

## Goal Types

| Goal Type | Module | Description |
|-----------|--------|-------------|
| `EntityStateChange` | `goalee.entity_goals` | Completes when any attribute of a single entity changes value |
| `EntityStateCondition` | `goalee.entity_goals` | Completes when a user-defined condition (lambda or string expression) evaluates to true |
| `EntityAttrStream` | `goalee.entity_goals` | Monitors a stream of attribute values against an expected sequence, with strategies (ALL, NONE, AT_LEAST_ONE, JUST_ONE, EXACTLY_X, ordered variants) |
| `RectangleAreaGoal` | `goalee.area_goals` | Checks whether entities enter or avoid a rectangular region defined by a corner point and dimensions |
| `CircularAreaGoal` | `goalee.area_goals` | Checks whether entities enter or avoid a circular region defined by a center point and radius |
| `MovingAreaGoal` | `goalee.area_goals` | Circular area goal where the center follows a motion entity's position in real time |
| `PoseGoal` | `goalee.pose_goals` | Completes when an entity reaches a target position and orientation within deviation tolerances |
| `PositionGoal` | `goalee.pose_goals` | Completes when an entity reaches a target 3D position (x, y, z) within a deviation tolerance |
| `OrientationGoal` | `goalee.pose_goals` | Completes when an entity reaches a target orientation (roll, pitch, yaw) within a deviation tolerance |
| `WaypointTrajectoryGoal` | `goalee.trajectory_goals` | Completes when an entity visits all waypoints in order, each within a deviation tolerance |
| `ComplexGoal` | `goalee.complex_goal` | Composite goal that groups sub-goals and evaluates them with a configurable algorithm (see below) |
| `GoalRepeater` | `goalee.repeater` | Wraps any goal and runs it N times, completing only if every iteration succeeds |

### ComplexGoal Algorithms

| Algorithm | Behavior |
|-----------|----------|
| `ALL_ACCOMPLISHED` | All sub-goals must complete (concurrent execution) |
| `ALL_ACCOMPLISHED_ORDERED` | All sub-goals must complete in declaration order (sequential execution) |
| `NONE_ACCOMPLISHED` | No sub-goal may complete |
| `AT_LEAST_ONE_ACCOMPLISHED` | At least one sub-goal must complete |
| `EXACTLY_X_ACCOMPLISHED` | Exactly X sub-goals must complete (concurrent execution) |
| `EXACTLY_X_ACCOMPLISHED_ORDERED` | Exactly X sub-goals must complete in order (sequential execution) |

## Broker Configuration

All broker models inherit from `Broker` (a pydantic `BaseModel`).

| Broker | Fields | Defaults |
|--------|--------|----------|
| `RedisBroker` | `host`, `port`, `db`, `username`, `password` | `localhost`, `6379`, `0`, `""`, `""` |
| `MQTTBroker` | `host`, `port`, `username`, `password` | `localhost`, `1883`, `""`, `""` |
| `AMQPBroker` | `host`, `port`, `vhost`, `username`, `password` | `localhost`, `5672`, `"/"`, `"guest"`, `"guest"` |

```python
from goalee import RedisBroker, MQTTBroker, AMQPBroker

redis = RedisBroker(host="redis.local", port=6379, db=0)
mqtt = MQTTBroker(host="mqtt.local", port=1883)
amqp = AMQPBroker(host="rabbitmq.local", port=5672, vhost="/")
```

## Scenario Execution

A `Scenario` accepts three categories of goals:

- **goals** ... the primary verification targets, scored with configurable weights.
- **anti_goals** ... negative conditions. Their weighted score is subtracted from the total.
- **fatal_goals** ... if any fatal goal completes, all other goals are terminated immediately.

Two execution modes are available:

- **`run_seq()`** runs goals one at a time, in the order they were added. If a fatal goal triggers, remaining goals are skipped.
- **`run_concurrent()`** runs all goals in parallel using a thread pool. Goals execute independently until they reach a terminal state or time out.

Both modes start entities, run anti-goals and fatal goals in background threads, compute a final weighted score, and clean up resources on completion.

## Goal Lifecycle

Every goal follows this state machine:

```
IDLE -> RUNNING -> COMPLETED | FAILED | TERMINATED
```

- **IDLE**: initial state before execution begins.
- **RUNNING**: the goal is actively ticking and evaluating its condition.
- **COMPLETED**: the goal's condition was satisfied.
- **FAILED**: the goal timed out (`max_duration` exceeded), finished too quickly (`min_duration` not met), or its condition was not satisfied.
- **TERMINATED**: the goal was stopped externally (e.g., by a fatal goal triggering).

### Timing Parameters

| Parameter | Effect |
|-----------|--------|
| `max_duration` | Maximum seconds the goal can run. Exceeding this causes FAILED. |
| `min_duration` | Minimum seconds the goal must run. Completing before this causes FAILED. |
| `for_duration` | The condition must hold continuously for this many seconds before the goal transitions to COMPLETED. If the condition drops, the timer resets. |

## Configuration

Goalee reads configuration from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOALDSL_ZERO_LOGS` | Disable all logging (set to `1` to suppress) | `0` |
| `GOALDSL_LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `"INFO"` |
| `GOAL_TICK_FREQ_HZ` | Goal tick frequency in Hz | `10` |

## Examples

The `examples/` directory contains runnable demo scenarios. Each example includes an `app.py` (data publisher) and a `goal_checker.py` (goal definitions and scenario).

| Example | Description |
|---------|-------------|
| `entity_goals` | Basic entity state condition and state change goals |
| `area_goals` | Rectangular and circular area enter/avoid goals |
| `area_for_time` | Area goals with `for_duration` hold-time constraints |
| `pose_goals` | Position, orientation, and combined pose goals |
| `waypoint_trajectory_goal` | Waypoint trajectory tracking |
| `complex_goal` | Composite goals with different algorithms |
| `entity_attr_stream` | Attribute stream monitoring with match strategies |
| `entity_for_time` | Entity condition goals with hold-time constraints |
| `goal_repeater` | Running a goal multiple times with GoalRepeater |
| `moving_area_goal` | Circular area that follows a moving entity |
| `anti_goals` | Anti-goal scoring (negative conditions) |
| `fatal_goals` | Fatal goals that terminate all other goals on completion |

## Development

Install with development and test dependencies:

```bash
pip install -e ".[dev,test]"
```

Available make targets:

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter on `goalee/` and `tests/` |
| `make format` | Run ruff formatter on `goalee/` and `tests/` |
| `make test` | Run pytest test suite |
| `make docs` | Build Sphinx HTML documentation |
| `make dist` | Build sdist and wheel packages |
| `make clean` | Remove build artifacts, caches, and test output |

## Testing

The test suite contains 447 tests with 99% code coverage. Tests mock commlib-py internals, so no running broker is required.

```bash
make test
```

Or run with coverage reporting:

```bash
coverage run -m pytest tests/ -v && coverage report -m
```

## GoalDSL Ecosystem

Goalee is the runtime verification engine for [GoalDSL](https://github.com/robotics-4-all/goal-dsl), a domain-specific language for specifying verification goals over Cyber-Physical Systems. The GoalDSL code generator produces goalee Python code from high-level goal specifications. You can also use goalee directly as a standalone Python library without the DSL layer.

## License

MIT
