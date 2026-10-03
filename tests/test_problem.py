"""Every generated problem must be solvable and honestly labelled."""

import random

import pytest

from mathcastle.constants import TIME_LIMIT, TOTAL_LEVELS
from mathcastle.problem import MathProblem, ProblemGenerator

LEVELS = range(1, TOTAL_LEVELS + 1)
SAMPLES = 200


@pytest.mark.parametrize("level", LEVELS)
def test_the_answer_is_exactly_what_the_question_asks(level):
    generator = ProblemGenerator()
    for _ in range(SAMPLES):
        problem = generator.generate(level)
        assert eval(problem.question) == problem.answer
        assert isinstance(problem.answer, int)


@pytest.mark.parametrize("level", LEVELS)
def test_problems_report_their_level_and_share_the_time_limit(level):
    problem = ProblemGenerator().generate(level)
    assert problem.difficulty == level
    assert problem.time_limit == TIME_LIMIT


@pytest.mark.parametrize("level", LEVELS)
def test_questions_only_use_operators_that_parse_as_python(level):
    generator = ProblemGenerator()
    for _ in range(SAMPLES):
        question = generator.generate(level).question
        assert question
        assert eval(question, {"__builtins__": {}}, {}) is not None


def test_the_first_level_stays_on_single_digit_arithmetic():
    generator = ProblemGenerator()
    problems = [generator.generate(1) for _ in range(SAMPLES)]
    for problem in problems:
        assert "*" not in problem.question
        assert "/" not in problem.question
        assert abs(problem.answer) < 20


def test_the_last_level_asks_harder_questions():
    generator = ProblemGenerator()
    problems = [generator.generate(TOTAL_LEVELS) for _ in range(SAMPLES)]
    assert any("*" in problem.question for problem in problems)
    assert any(problem.answer < 0 for problem in problems)


def test_the_middle_level_includes_exact_division():
    generator = ProblemGenerator()
    questions = [generator.generate(3).question for _ in range(SAMPLES)]
    assert any("/" in question for question in questions)


def test_a_seeded_generator_is_reproducible():
    first = ProblemGenerator().generate(3, random.Random(7))
    second = ProblemGenerator().generate(3, random.Random(7))
    assert (first.question, first.answer) == (second.question, second.answer)


def test_two_draws_from_the_generator_are_independent_objects():
    generator = ProblemGenerator()
    assert generator.generate(2) is not generator.generate(2)


def test_an_unknown_level_falls_back_instead_of_raising():
    problem = ProblemGenerator().generate(99)
    assert isinstance(problem, MathProblem)
    assert problem.difficulty == 1


def test_check_accepts_only_the_expected_answer():
    problem = MathProblem("7 * 6", 42, difficulty=1)
    assert problem.check(42) is True
    assert problem.check(41) is False


def test_the_time_limit_trips_exactly_on_the_limit():
    problem = MathProblem("7 * 6", 42, difficulty=1)
    assert problem.is_timeout(14.9) is False
    assert problem.is_timeout(15.0) is True
    assert problem.is_timeout(15.1) is True
