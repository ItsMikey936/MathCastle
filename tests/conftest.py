"""Shared test fixtures."""

import pytest


class FakeClock:
    """A clock that only moves when a test tells it to."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock forward."""
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    """A clock under the test's control, so nothing ever sleeps."""
    return FakeClock()
