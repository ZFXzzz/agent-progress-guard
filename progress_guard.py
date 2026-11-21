"""Track an agent's no-progress timeout separately from its task deadline."""

from enum import Enum
from math import isfinite


class Observation(Enum):
    PROGRESS = "progress"
    EMPTY_RESULT = "empty_result"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    COMPLETE = "complete"


class Decision(Enum):
    CONTINUE = "continue"
    COMPLETE = "complete"
    NO_PROGRESS = "no_progress"
    DEADLINE_EXCEEDED = "deadline_exceeded"


class ProgressGuard:
    """Consume timestamped observations for one task in monotonic time."""

    def __init__(
        self,
        *,
        now: float,
        no_progress_timeout: float,
        task_timeout: float,
    ) -> None:
        if not isfinite(now):
            raise ValueError("The start timestamp must be finite")
        if not isfinite(no_progress_timeout) or no_progress_timeout <= 0:
            raise ValueError("The no-progress timeout must be finite and positive")
        if not isfinite(task_timeout) or task_timeout <= 0:
            raise ValueError("The task timeout must be finite and positive")

        self._start = now
        self._last_update = now
        self._no_progress_timeout = no_progress_timeout
        self._task_timeout = task_timeout
        self._stall_elapsed = 0.0
        self._dependency_unavailable = False
        self._decision = Decision.CONTINUE

    def update(self, now: float, observation: Observation | None = None) -> Decision:
        """Advance time to `now` and apply an optional observation at that instant."""
        if not isfinite(now) or now < self._last_update:
            raise ValueError("Timestamps must be finite and nondecreasing")
        if observation is not None and not isinstance(observation, Observation):
            raise ValueError("Use an Observation member or None")
        if self._decision is not Decision.CONTINUE:
            self._last_update = now
            return self._decision

        if not self._dependency_unavailable:
            self._stall_elapsed += now - self._last_update
        self._last_update = now

        if now - self._start >= self._task_timeout:
            self._decision = Decision.DEADLINE_EXCEEDED
        elif self._stall_elapsed >= self._no_progress_timeout:
            self._decision = Decision.NO_PROGRESS
        elif observation is Observation.COMPLETE:
            self._decision = Decision.COMPLETE
        elif observation is not None:
            self._dependency_unavailable = observation is Observation.DEPENDENCY_UNAVAILABLE
            if observation is Observation.PROGRESS:
                self._stall_elapsed = 0.0

        return self._decision
