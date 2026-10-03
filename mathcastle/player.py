"""The player character."""

from __future__ import annotations

from mathcastle.constants import STARTING_LIFE_POINTS


class Player:
    """Life points and gold. The gold carried out is the final score."""

    def __init__(
        self,
        life_points: int = STARTING_LIFE_POINTS,
        gold: int = 0,
    ) -> None:
        self.life_points = life_points
        self.gold = gold

    def take_damage(self, points: int) -> None:
        """Lose life points, never dropping below zero."""
        self.life_points = max(0, self.life_points - points)

    def add_gold(self, points: int) -> None:
        """Collect gold."""
        self.gold += points

    def is_alive(self) -> bool:
        """True while the player still has life points left."""
        return self.life_points > 0

    def __repr__(self) -> str:
        return f"Player(life_points={self.life_points}, gold={self.gold})"
