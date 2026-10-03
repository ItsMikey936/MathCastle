"""One timed attempt at solving a math problem."""

from __future__ import annotations

import time
from collections.abc import Callable

from mathcastle.problem import MathProblem

#: Source of the current time in seconds. Injected for testability.
Clock = Callable[[], float]


class Challenge:
    """Wraps a problem in a countdown driven by an injectable clock.

    Injecting the clock is what makes the engine testable: tests pass a
    fake they can move forward at will, so the deadline is exercised
    without sleeping and without any UI involved.
    """

    def __init__(
        self,
        problem: MathProblem,
        clock: Clock = time.monotonic,
    ) -> None:
        self.problem = problem
        self._clock = clock
        self._started_at = clock()

    def elapsed(self) -> float:
        """Seconds since the challenge started."""
        return self._clock() - self._started_at

    def remaining(self) -> float:
        """Seconds left, never below zero."""
        return max(0.0, self.problem.time_limit - self.elapsed())

    def expired(self) -> bool:
        """True once the time limit is gone."""
        return self.problem.is_timeout(self.elapsed())

    def tick(self) -> bool:
        """Return True when the deadline blew on this tick.

        The challenge only reports the fact; the engine owns the damage.
        """
        return self.expired()

    def fraction_left(self) -> float:
        """Remaining time as a 0..1 ratio, for progress bars."""
        return self.remaining() / self.problem.time_limit

    def __repr__(self) -> str:
        return f"Challenge({self.problem!r})"
