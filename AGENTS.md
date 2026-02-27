# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-27
**Commit:** 28e8ef7
**Branch:** devel

## OVERVIEW

Python 3.9+ library implementing goal-driven runtime verification for Cyber-Physical Systems. Part of the [GoalDSL](https://github.com/robotics-4-all/goal-dsl) ecosystem — used as the runtime target for generated code. Core stack: `commlib-py` (pub/sub messaging), `pydantic` (broker models).

## STRUCTURE

```
goalee/
├── goalee/                      # Core library (14 modules) — see goalee/AGENTS.md
├── examples/                    # 12 demo scenarios (each: app.py + goal_checker.py)
├── tests/                       # pytest smoke tests (imports, enums, brokers, types)
├── docs/                        # Sphinx docs (mostly boilerplate)
├── pyproject.toml               # Package metadata, deps, ruff + pytest config
├── Makefile                     # lint/format/test/docs/dist/install targets
└── .github/workflows/           # CI (test matrix 3.9-3.13) + PyPI publish
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new goal type | `goalee/` | Subclass `Goal`, implement `on_enter()` + `tick()` |
| Add broker transport | `goalee/brokers.py` + `goalee/entity.py` | Broker = pydantic model; `Entity.create_node()` uses `isinstance` dispatch |
| Understand execution flow | `goalee/scenario.py` | `run_seq()` / `run_concurrent()` orchestrate goals |
| Entity data subscription | `goalee/entity.py` | Uses `commlib-py` Node + Subscriber pattern |
| Runtime events/monitoring | `goalee/rtmonitor.py` | Publishes `EventMsg` / `LogMsg` via commlib |
| Spatial/geometric goals | `goalee/area_goals.py`, `goalee/pose_goals.py` | Rectangle, Circular, Moving area + Pose/Position/Orientation |
| Composite goal logic | `goalee/complex_goal.py` | `ComplexGoalAlgorithm` enum: ALL, NONE, AT_LEAST_ONE, EXACTLY_X (+ ordered variants) |
| Goal repetition | `goalee/repeater.py` | Wraps any Goal, runs N times |
| Example patterns | `examples/*/goal_checker.py` | All follow: create broker -> entities -> goals -> scenario -> run |
| Configuration | `goalee/definitions.py` | Env vars: `GOALDSL_ZERO_LOGS`, `GOALDSL_LOG_LEVEL`, `GOAL_TICK_FREQ_HZ` |
| CI/CD | `.github/workflows/` | `ci.yml` (lint+test matrix), `publish.yml` (PyPI on release) |

## CONVENTIONS

- **Python 3.9+**: `from __future__ import annotations` in all modules. Modern type hints (`list[X]`, `X | None`).
- **Linting**: ruff configured in `pyproject.toml`. Run `make lint` / `make format`.
- **Broker dispatch via isinstance**: `isinstance(broker, RedisBroker)` in `entity.py` and `scenario.py`.
- **Logging**: Custom wrapper in `goalee/logging.py` using stdlib `logging`. Each class has `log_info/warning/error/debug` methods with `[ClassName:name]` prefix.
- **Private-by-convention**: All internal state uses `_` prefix. Properties expose read-only access.
- **Goal lifecycle**: `IDLE -> RUNNING -> COMPLETED|FAILED|TERMINATED`. State machine in `Goal.set_state()`.
- **Threading**: `concurrent.futures.ThreadPoolExecutor` for concurrent goal execution. Fatal goals run in separate threads and can terminate all goals.

## ANTI-PATTERNS (THIS PROJECT)

- `eval()` used in `entity_goals.py:EntityStateCondition.evaluate_condition()` — intentional for DSL-generated code, marked with SAFETY comment.
- Env var prefix is `GOALDSL_*` (not `GOALEE_*`) — reflects origin as GoalDSL runtime.

## COMMANDS

```bash
pip install .                    # Install package
pip install -e ".[dev,test]"     # Dev install with extras
make lint                        # ruff check goalee/ tests/
make format                      # ruff format goalee/ tests/
make test                        # pytest tests/ -v
make clean                       # Remove build/pyc/test/ruff artifacts
make docs                        # Sphinx HTML docs
make dist                        # python -m build (sdist + wheel)
```

## NOTES

- `commlib-py>=0.10.6` is the messaging backbone — supports Redis, MQTT, AMQP transports.
- `pydantic>=2.0.0` only used for Broker models (4 simple dataclasses).
- PyPI publishing via GitHub Actions trusted publisher (OIDC) — triggered on GitHub release.
