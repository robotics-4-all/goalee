# GOALEE CORE LIBRARY

Runtime goal verification engine. All goal types, entity management, broker integration, and scenario orchestration live here.

## STRUCTURE

```
goalee/
├── goal.py              # Base Goal class + GoalState enum (lifecycle FSM)
├── scenario.py          # Scenario orchestrator (seq/concurrent execution, scoring)
├── entity.py            # Entity: pub/sub data source, state tracking, attribute buffers
├── brokers.py           # Broker models: MQTT, AMQP, Redis (pydantic BaseModel)
├── entity_goals.py      # EntityStateChange, EntityStateCondition, EntityAttrStream
├── area_goals.py        # RectangleAreaGoal, CircularAreaGoal, MovingAreaGoal
├── pose_goals.py        # PoseGoal, PositionGoal, OrientationGoal
├── trajectory_goals.py  # WaypointTrajectoryGoal
├── complex_goal.py      # ComplexGoal: composite goals with algorithms (ALL, NONE, AT_LEAST_ONE, EXACTLY_X)
├── repeater.py          # GoalRepeater: run a goal N times
├── rtmonitor.py         # RTMonitor: real-time event/log publishing via commlib
├── types.py             # Point, Orientation, Pose dataclasses with math ops
├── definitions.py       # Global config from env vars
├── logging.py           # Logging setup (stdlib, configurable via GOALDSL_* env vars)
└── exception.py         # UnknownException (unused stub)
```

## WHERE TO LOOK

| Task | Start here | Key methods |
|------|-----------|-------------|
| New goal type | `goal.py` | Subclass `Goal`, implement `on_enter()`, `tick()`, optionally `on_exit()`, `on_reset()` |
| Goal state logic | `goal.py` | `run_until_exit()` — tick loop with timeout/min_duration checks |
| Condition-based goals | `entity_goals.py` | `EntityStateCondition.tick()` — lambda or string eval |
| Spatial checks | `area_goals.py` | `check_area()` on each subclass — position-in-region tests |
| Composite goals | `complex_goal.py` | `calc_result()` + `_evaluate_results()` — algorithm dispatch |
| Scenario lifecycle | `scenario.py` | `run_seq()`/`run_concurrent()` → start entities → run goals → score → cleanup |
| Entity data flow | `entity.py` | `start()` → `create_node()` → commlib subscriber → `update_state()` callback |
| Broker wiring | `entity.py:create_node()` | `isinstance`-based dispatch to transport-specific `ConnectionParameters` |

## CONVENTIONS

- **Goal contract**: Every Goal subclass MUST implement `on_enter()` and `tick()`. `tick()` is called in a loop by `run_until_exit()` at `_freq` Hz.
- **for_duration pattern**: Goals supporting hold-time use `_ts_hold` timestamp. Set on first condition match, check elapsed on subsequent ticks, reset to `-1.0` on condition loss.
- **Entity attribute access**: `entity.attributes['key']` or `entity['key']` (via `__getitem__`). Attributes are flat dicts updated via pub/sub callback.
- **Condition functions**: `EntityStateCondition` accepts lambda (receives entity map `{name: Entity}`) or string (eval'd with `CONDITION_FUNCTIONS` as locals).
- **Serialization**: `Goal.serialize()` returns dict. `ComplexGoal` and `GoalRepeater` extend with nested goal serialization.

## ANTI-PATTERNS (THIS MODULE)

- **Broker dispatch duplication**: `entity.py:create_node()` and `scenario.py:_create_comm_node()` have near-identical `isinstance` dispatch for transport selection. Changes to one must be mirrored.
- **`eval()` in conditions**: `entity_goals.py:evaluate_condition()` uses `eval()` on user strings. Intentional for DSL-generated code, marked with SAFETY comment.
- **Silent failures**: `entity.py:update_state()` silently skips unknown keys in non-strict mode.
