# Agent progress guard

A small Python reference for agents that call search, retrieval, or other
external dependencies. A successful query can return no matches. A timeout
or unavailable dependency needs its own outcome so the agent can pause its
no-progress timer while keeping the task deadline in force.

| Observation | Effect on the no-progress timer |
|---|---|
| `EMPTY_RESULT` | Resume counting from the remaining budget. The dependency responded and the task made no progress. |
| `DEPENDENCY_UNAVAILABLE` | Pause counting until the next successful observation. Repeated outages preserve the remaining budget. |
| `PROGRESS` | Reset the timer and resume counting. Use this for meaningful progress toward a result. |
| `COMPLETE` | Finish the task if its timeouts have not expired. |

Use one guard per task on the same monotonic clock. Call `update(now, event)` at
each observation and `update(now)` on periodic ticks so an idle or blocked
task can still time out. An observation takes effect at its timestamp. Time
before the first outage observation counts under the previous state. At a
timeout boundary the timeout takes effect before the incoming observation.
The task deadline takes precedence if both timeouts have elapsed at a tick.

## Example

```python
from progress_guard import Decision, Observation, ProgressGuard

guard = ProgressGuard(now=0, no_progress_timeout=5, task_timeout=20)

assert guard.update(2, Observation.EMPTY_RESULT) is Decision.CONTINUE
assert guard.update(3, Observation.DEPENDENCY_UNAVAILABLE) is Decision.CONTINUE
assert guard.update(11, Observation.EMPTY_RESULT) is Decision.CONTINUE
assert guard.update(12) is Decision.CONTINUE
assert guard.update(13) is Decision.NO_PROGRESS
```

The task used three seconds of its no-progress budget before the outage. Once
a successful empty result arrives, the remaining two seconds count again. In
an application, pass `time.monotonic()` in place of these synthetic times.
Use a caller-owned request timeout or cancellation to enforce the task
deadline while an external call is blocked.

## Run the tests

Python 3.10 or later. The tests use synthetic monotonic timestamps.

```sh
python -m unittest -v
```
