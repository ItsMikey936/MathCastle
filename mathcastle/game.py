"""The engine: doors, combat, damage, victory and defeat.

Nothing here knows that Streamlit exists. The UI calls in and reads the
public state; the engine never calls back.
"""

from __future__ import annotations

import random
import time

from mathcastle.challenge import Challenge, Clock
from mathcastle.constants import (
    STARTING_LIFE_POINTS,
    TOTAL_LEVELS,
)
from mathcastle.enums import GameState, Outcome
from mathcastle.level import Level
from mathcastle.player import Player
from mathcastle.problem import MathProblem, ProblemGenerator
from mathcastle.rooms import EnemyRoom, Room


class Game:
    """Drives a whole run of MathCastle."""

    def __init__(
        self,
        generator: ProblemGenerator | None = None,
        rng: random.Random | None = None,
        clock: Clock = time.monotonic,
    ) -> None:
        self._rng: random.Random = rng if rng is not None else random.Random()
        self._generator = generator or ProblemGenerator()
        self._clock = clock
        self.status = GameState.READY
        self.current_level = 1
        self.challenge: Challenge | None = None
        self._levels: list[Level] = []
        self._player = Player()
        self._combat_room: EnemyRoom | None = None
        self._last_room: Room | None = None
        self._challenge_serial = 0

    def start_new_game(self) -> None:
        """Deal a fresh castle and give the player a fresh start."""
        self._player = Player(life_points=STARTING_LIFE_POINTS)
        self._levels = [
            Level(number, self._generator, self._rng)
            for number in range(1, TOTAL_LEVELS + 1)
        ]
        self.current_level = 1
        self.challenge = None
        self._combat_room = None
        self._last_room = None
        self._challenge_serial = 0
        self.status = GameState.IN_PROGRESS

    @property
    def player(self) -> Player:
        """The player of the current run."""
        return self._player

    @property
    def levels(self) -> tuple[Level, ...]:
        """Every level dealt for this run."""
        return tuple(self._levels)

    @property
    def challenge_serial(self) -> int:
        """Bumped for every new problem, used to key the answer box."""
        return self._challenge_serial

    def level(self) -> Level:
        """The level the player is standing on."""
        return self._levels[self.current_level - 1]

    def choose_room(self, index: int) -> Outcome:
        """Open the door at ``index`` and report what was behind it.

        Raises ValueError when the door cannot be chosen because the game
        is not accepting doors, or because it is already known to be shut.
        Raises IndexError when there is no door at that position.
        """
        if self.status is GameState.READY:
            self.start_new_game()
        if self.status is not GameState.IN_PROGRESS:
            raise ValueError("doors cannot be chosen right now")
        level = self.level()
        if not 0 <= index < len(level.rooms):
            raise IndexError(f"there is no door at position {index}")
        room = level.get_room(index)
        if not room.is_choosable:
            raise ValueError(f"door {index} is already known to be shut")
        self._last_room = room
        outcome = room.enter(self._player)
        if outcome is Outcome.CHALLENGE:
            self._begin_combat(room)
        return outcome

    def submit_answer(self, raw: str) -> Outcome:
        """Answer the problem on screen.

        The deadline is enforced here rather than in the UI, so an answer
        that arrives late counts as wrong. Input that is not a whole
        number is rejected without costing life points.
        """
        if self.status is not GameState.IN_COMBAT or self.challenge is None:
            raise ValueError("there is no problem waiting for an answer")
        if self.challenge.expired():
            return self._settle(solved=False, expired=True)
        try:
            answer = int(str(raw).strip())
        except (TypeError, ValueError):
            return Outcome.INVALID
        return self._settle(solved=self.challenge.problem.check(answer))

    def tick(self) -> Outcome | None:
        """Apply the deadline if it blew. None when nothing happened.

        The UI calls this once a second; the engine remains the only place
        that decides the 15 second rule is over.
        """
        if self.status is not GameState.IN_COMBAT or self.challenge is None:
            return None
        if not self.challenge.tick():
            return None
        return self._settle(solved=False, expired=True)

    def _begin_combat(self, room: EnemyRoom) -> None:
        """Lock the level and present the enemy's first problem."""
        self._combat_room = room
        self._start_challenge(room.enemy.problem)
        self.status = GameState.IN_COMBAT

    def _start_challenge(self, problem: MathProblem) -> None:
        """Begin one timed attempt at a problem."""
        self._challenge_serial += 1
        self.challenge = Challenge(problem, self._clock)

    def _settle(self, solved: bool, expired: bool = False) -> Outcome:
        """Close one attempt: advance, lose a life, or die."""
        room = self._combat_room
        if room is None:
            raise RuntimeError("combat started without a room")
        outcome = room.resolve(self._player, solved)
        if solved:
            self._end_combat()
            if self.current_level >= TOTAL_LEVELS:
                self.status = GameState.VICTORY
            else:
                self.advance_level()
                self.status = GameState.IN_PROGRESS
            return outcome
        if not self._player.is_alive():
            self._end_combat()
            self.status = GameState.DEFEAT
            return Outcome.DEFEAT
        difficulty = room.enemy.problem.difficulty
        self._start_challenge(self._generator.generate(difficulty, self._rng))
        return Outcome.TIMEOUT if expired else outcome

    def _end_combat(self) -> None:
        """Drop the running problem and the room that started it."""
        self.challenge = None
        self._combat_room = None

    def advance_level(self) -> None:
        """Go down one floor, stopping at the last one."""
        if self.current_level < TOTAL_LEVELS:
            self.current_level += 1

    def narrate(self, outcome: Outcome) -> str:
        """Describe ``outcome`` in a sentence, for the player to read."""
        room = self._last_room
        enemy = getattr(room, "enemy", None)
        life = self._player.life_points
        if outcome is Outcome.CHALLENGE:
            return f"A {enemy.name} blocks the way. Solve it to pass."
        if outcome is Outcome.GOLD:
            amount = getattr(room, "gold_amount", 0)
            return f"You find {amount} gold coins. Total: {self._player.gold}."
        if outcome is Outcome.NOTHING:
            return "An empty room. Nothing to take, and no way onward."
        if outcome is Outcome.WALL:
            return "A dead end: a wall of stone blocks this passage."
        if outcome is Outcome.INVALID:
            return "That is not a whole number. The clock keeps running."
        if outcome is Outcome.COMBAT_WON:
            name = enemy.name
            level = self.current_level
            return f"You defeat the {name} and descend to level {level}."
        if outcome is Outcome.COMBAT_LOST:
            name, damage = enemy.name, enemy.damage
            return f"Wrong! The {name} hits you for {damage}. Life: {life}."
        if outcome is Outcome.TIMEOUT:
            name, damage = enemy.name, enemy.damage
            return f"Time is up! The {name} hits you for {damage}."
        if outcome is Outcome.DEFEAT:
            gold = self._player.gold
            return f"You fall in the castle. Final score: {gold} gold."
        return ""

    def is_victory(self) -> bool:
        """True once the enemy of the last level has been defeated."""
        return self.status is GameState.VICTORY

    def is_over(self) -> bool:
        """True once the run can no longer continue."""
        return self.status in (GameState.VICTORY, GameState.DEFEAT)
