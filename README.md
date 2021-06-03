# goalee

Goalee is a Python 3.5+ library that implements several concepts of [GoalDSL](https://github.com/robotics-4-all/goal-dsl) and it is used by
the code generator to produce the source code from a given Goaldsl model.
Goalee can also be used as a standalone Python library for implementing goal-driven targets for applications.


# Table of contents
1. [Installation](#installation)
2. [Quick Start](#quickstart)
2. [Examples](#examples)

## Installation <a name="installation"></a>

Download this repository and simply install using `pip` package manager.

```
git clone https://github.com/robotics-4-all/goalee
cd goalee
pip install .
```


## Quick Start <a name="quickstart"></a>


The source code of a goal validator is shown below. Two Goals are defined,
a `TopicMessageParamGoal` and a `TopicMessageReceivedGoal`.

```
#!/usr/bin/env python3

from goalee import Target, RedisMiddleware
from goalee.topic_goals import TopicMessageReceivedGoal, TopicMessageParamGoal


if __name__ == '__main__':
    middleware = RedisMiddleware()
    t = Target(middleware)

    g1 = TopicMessageReceivedGoal(topic='sensors.sonar.front',
                                  max_duration=10.0)
    g2 = TopicMessageParamGoal(topic='sensors.sonar.front',
                               max_duration=10.0,
                               condition=lambda msg: True if msg['range'] > 5 \
                               else False)
    t.add_goal(g1)
    t.add_goal(g2)

    t.run_seq()
```

The first goal waits for a message to be received at topic
`sensors.sonar.front`, for a maximum duration of 10 seconds, while the second
goal uses a condition to filter messages arrived at `sensors.sonar.front`. In
this example `g2` completes when a message that satisfies the condition `range > 5` arrives.
Conditions are defined using `lambda` functions in Python.

After creation of goal instances, you have to create a target and add goals to
it. Target requires a Middleware to connect to and listen to topics. In the
above example a local Redis is used as the communication middleware.

```
middleware = RedisMiddleware()
t = Target(middleware)

```

Targets can be executed in **Concurrent** (`t.run_concurrent()`) or **Sequential** (`t.run_seq()`) mode. In sequential
mode goals are executed in the order they were added using the `add_goal`
method.


## Examples <a name="examples"></a>

Several examples can be found [here](./examples/).

