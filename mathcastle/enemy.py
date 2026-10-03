"""Enemies guarding the enemy room."""

from __future__ import annotations

from mathcastle.player import Player
from mathcastle.problem import MathProblem

#: Enemy names dealt at random on every level.
ENEMY_NAMES = (
    "Goblin",
    "Skeleton",
    "Witch",
    "Giant Spider",
    "Cave Troll",
)


class Enemy:
    """A guard that asks a math problem and hits back on failure."""

    def __init__(self, name: str, damage: int, problem: MathProblem) -> None:
        self.name = name
        self.damage = damage
        self.problem = problem

    def attack(self, player: Player) -> None:
        """Deal this enemy's damage to the player."""
        player.take_damage(self.damage)

    def __repr__(self) -> str:
        return f"Enemy({self.name!r}, damage={self.damage})"
