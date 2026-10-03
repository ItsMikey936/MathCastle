"""Math problems and the level-based generator that builds them.

Questions are built as plain Python expressions (``+ - * / **`` and
parentheses). That keeps the wording unambiguous and lets the test suite
verify every answer by evaluating the question itself instead of trusting
a hardcoded key.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from mathcastle.constants import TIME_LIMIT

#: An operation returns the question to show and its answer.
Operation = Callable[[random.Random], tuple[str, int]]


class MathProblem:
    """One arithmetic question with a time limit."""

    def __init__(
        self,
        question: str,
        answer: int,
        difficulty: int,
        time_limit: int = TIME_LIMIT,
    ) -> None:
        self.question = question
        self.answer = answer
        self.difficulty = difficulty
        self.time_limit = time_limit

    def check(self, answer: int) -> bool:
        """Return True when ``answer`` is the expected one."""
        return answer == self.answer

    def is_timeout(self, elapsed: float) -> bool:
        """Return True when ``elapsed`` seconds exhaust the limit."""
        return elapsed >= self.time_limit

    def __repr__(self) -> str:
        return f"MathProblem({self.question!r}, answer={self.answer})"


def _add_single_digit(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(1, 9), rng.randint(1, 9)
    return f"{a} + {b}", a + b


def _subtract_single_digit(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(2, 9), rng.randint(1, 9)
    return f"{a} - {b}", a - b


def _multiply_single_digit(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    return f"{a} * {b}", a * b


def _add_two_digit(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(10, 49), rng.randint(10, 49)
    return f"{a} + {b}", a + b


def _subtract_two_digit(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(20, 99), rng.randint(10, 20)
    return f"{a} - {b}", a - b


def _exact_division(rng: random.Random) -> tuple[str, int]:
    divisor, quotient = rng.randint(2, 9), rng.randint(2, 12)
    return f"{divisor * quotient} / {divisor}", quotient


def _long_division(rng: random.Random) -> tuple[str, int]:
    divisor, quotient = rng.randint(3, 9), rng.randint(11, 20)
    return f"{divisor * quotient} / {divisor}", quotient


def _square(rng: random.Random) -> tuple[str, int]:
    base = rng.randint(2, 9)
    return f"{base} ** 2", base * base


def _parenthesised_product(rng: random.Random) -> tuple[str, int]:
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 5)
    return f"({a} + {b}) * {c}", (a + b) * c


def _mixed_two_step(rng: random.Random) -> tuple[str, int]:
    a, b, c, d = (
        rng.randint(2, 9),
        rng.randint(2, 9),
        rng.randint(2, 5),
        rng.randint(2, 12),
    )
    return f"{a} + {b} * {c} - {d}", a + b * c - d


def _negative_result(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(2, 9), rng.randint(10, 20)
    return f"{a} - {b}", a - b


def _squares_difference(rng: random.Random) -> tuple[str, int]:
    a, b = rng.randint(2, 6), rng.randint(2, 6)
    return f"{a} ** 2 - {b} ** 2", a * a - b * b


#: Operations available on each level. Difficulty grows with the number.
DEFAULT_OPERATIONS_BY_LEVEL: dict[int, tuple[Operation, ...]] = {
    1: (_add_single_digit, _subtract_single_digit),
    2: (_multiply_single_digit, _add_two_digit, _subtract_two_digit),
    3: (
        _exact_division,
        _long_division,
        _square,
        _parenthesised_product,
    ),
    4: (
        _mixed_two_step,
        _negative_result,
        _squares_difference,
        _long_division,
    ),
}

#: Level used when asked for one the generator does not know.
DEFAULT_LEVEL = 1


class ProblemGenerator:
    """Builds problems whose difficulty grows with the level."""

    def __init__(
        self,
        operations_by_level: dict[int, tuple[Operation, ...]] | None = None,
    ) -> None:
        self.operations_by_level = dict(
            operations_by_level or DEFAULT_OPERATIONS_BY_LEVEL
        )

    def generate(
        self,
        level: int,
        rng: random.Random | None = None,
    ) -> MathProblem:
        """Return a fresh random problem for ``level``.

        ``rng`` makes generation reproducible in tests. It only needs to
        provide ``choice``, ``randint`` and ``shuffle``, which the
        ``random`` module itself does.
        """
        source: random.Random = rng if rng is not None else random
        operations = self.operations_by_level.get(level)
        if not operations:
            level = DEFAULT_LEVEL
            operations = self.operations_by_level[level]
        question, answer = source.choice(list(operations))(source)
        return MathProblem(question, answer, difficulty=level)
