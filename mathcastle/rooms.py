"""Rooms: the doors the player picks from."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mathcastle.enemy import Enemy
from mathcastle.enums import Outcome, RoomType
from mathcastle.player import Player


class Room(ABC):
    """Base class for every door in the castle.

    A room's type is hidden until it is entered. Once entered, ``visited``
    turns True and the map is allowed to reveal what was behind it.
    """

    def __init__(self, room_type: RoomType) -> None:
        self.room_type = room_type
        self.visited = False

    @abstractmethod
    def enter(self, player: Player) -> Outcome:
        """Resolve entering the room and report what happened."""

    def mark_visited(self) -> None:
        """Flag the room as explored."""
        self.visited = True

    def __repr__(self) -> str:
        state = "visited" if self.visited else "unvisited"
        return f"{type(self).__name__}({state})"


class GoldRoom(Room):
    """A treasure room: gold, no challenge, and no way onward."""

    def __init__(self, gold_amount: int) -> None:
        super().__init__(RoomType.GOLD)
        self.gold_amount = gold_amount

    def enter(self, player: Player) -> Outcome:
        self.mark_visited()
        player.add_gold(self.gold_amount)
        return Outcome.GOLD


class EmptyRoom(Room):
    """Nothing here. The player comes back to the same level."""

    def __init__(self) -> None:
        super().__init__(RoomType.EMPTY)

    def enter(self, player: Player) -> Outcome:
        self.mark_visited()
        return Outcome.NOTHING


class EnemyRoom(Room):
    """The only way onward, and there is no way back.

    Entering is final: the room is marked visited at once and the player
    must defeat the enemy to leave it. There is no door out for the gold
    that may sit on the level they just skipped.
    """

    def __init__(self, enemy: Enemy) -> None:
        super().__init__(RoomType.ENEMY)
        self.enemy = enemy
        self.defeated = False

    def enter(self, player: Player) -> Outcome:
        self.mark_visited()
        return Outcome.CHALLENGE

    def resolve(self, player: Player, solved: bool) -> Outcome:
        """Settle one attempt and report the outcome.

        Losing costs life points. The engine then serves a brand new
        problem, so a losing streak is survivable until it is not.
        """
        if solved:
            self.defeated = True
            return Outcome.COMBAT_WON
        self.enemy.attack(player)
        return Outcome.COMBAT_LOST
