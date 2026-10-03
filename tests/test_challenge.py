"""The countdown, driven by a clock nobody has to wait for."""

import pytest

from mathcastle.challenge import Challenge
from mathcastle.constants import TIME_LIMIT
from mathcastle.problem import MathProblem


def make_challenge(clock) -> Challenge:
    """A challenge on the simplest problem there is."""
    return Challenge(MathProblem("1 + 1", 2, difficulty=1), clock)


def test_the_clock_starts_when_the_challenge_is_created(clock):
    challenge = make_challenge(clock)
    assert challenge.elapsed() == 0.0
    assert challenge.remaining() == TIME_LIMIT
    assert challenge.expired() is False


def test_the_remaining_time_counts_down(clock):
    challenge = make_challenge(clock)
    clock.advance(5)
    assert challenge.remaining() == TIME_LIMIT - 5


def test_the_remaining_time_never_goes_negative(clock):
    challenge = make_challenge(clock)
    clock.advance(TIME_LIMIT * 10)
    assert challenge.remaining() == 0.0


def test_the_challenge_expires_exactly_on_the_limit(clock):
    challenge = make_challenge(clock)
    clock.advance(TIME_LIMIT - 0.1)
    assert challenge.tick() is False
    assert challenge.expired() is False
    clock.advance(0.1)
    assert challenge.tick() is True
    assert challenge.expired() is True


def test_the_fraction_left_serves_a_progress_bar(clock):
    challenge = make_challenge(clock)
    assert challenge.fraction_left() == 1.0
    clock.advance(TIME_LIMIT / 2)
    assert challenge.fraction_left() == pytest.approx(0.5)
    clock.advance(TIME_LIMIT * 10)
    assert challenge.fraction_left() == 0.0


def test_each_challenge_starts_its_own_countdown(clock):
    first = make_challenge(clock)
    clock.advance(TIME_LIMIT + 1)
    second = make_challenge(clock)
    assert first.expired() is True
    assert second.expired() is False


def test_the_challenge_holds_on_to_its_problem(clock):
    problem = MathProblem("2 * 3", 6, difficulty=1)
    challenge = Challenge(problem, clock)
    assert challenge.problem is problem
    assert challenge.problem.check(6) is True
