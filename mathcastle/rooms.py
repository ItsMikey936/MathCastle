"""Rooms: the doors the player picks from.

Fog of war lives here. A room keeps its type to itself until the player
learns it, either by opening the door or by bumping into a wall. The
interface never reads a room's type: it asks for ``public_label``, so a
hidden room cannot leak even by accident.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mathcastle.enemy import Enemy
from mathcastle.enums import Outcome, RoomType
from mathcastle.player import Player

#: What a door says while the fog is still on it.
FOG_LABEL = "🚪 ?"


class Room(ABC):
    """Base class for every door in the castle.

    Two flags record how much the player knows. ``revealed`` means the
    fog has lifted, which happens either by opening the door or by
    finding a wall. ``visited`` means the player actually went in.

    Opening implies revealing, so exactly one state has revealed but not
    visited: a wall. The two flags can never contradict each other.
    """

    def __init__(self, room_type: RoomType) -> None:
        self.room_type = room_type
        self.revealed = False
        self.visited = False

    @abstractmethod
    def enter(self, player: Player) -> Outcome:
        """Resolve entering the room and report what happened."""

    def reveal(self) -> None:
        """Lift the fog without opening the door."""
        self.revealed = True

    def mark_visited(self) -> None:
        """Flag the room as explored. Opening a door reveals it too."""
        self.visited = True
        self.revealed = True

    @property
    def is_choosable(self) -> bool:
        """True while the door is fogged: the only kind left to open."""
        return not self.revealed

    def public_label(self) -> str:
        """The text to paint on the door, safe to show the player.

        A fogged door says nothing at all about what is behind it. Once
        revealed, the room is named by type, because the player already
        knows it.
        """
        if not self.revealed:
            return FOG_LABEL
        return self._revealed_label()

    @abstractmethod
    def _revealed_label(self) -> str:
        """Name the room once its type is no longer a secret."""

    def __repr__(self) -> str:
        """Anonymous while fogged, so a stray log cannot leak the layout."""
        if not self.revealed:
            return "Room(fogged)"
        state = "visited" if self.visited else "revealed"
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

    def _revealed_label(self) -> str:
        return f"💰 {self.gold_amount} gold"


class EmptyRoom(Room):
    """Nothing here. The player comes back to the same level."""

    def __init__(self) -> None:
        super().__init__(RoomType.EMPTY)

    def enter(self, player: Player) -> Outcome:
        self.mark_visited()
        return Outcome.NOTHING

    def _revealed_label(self) -> str:
        return "🫙 empty"


class WallRoom(Room):
    """A blocked passage: it costs nothing and lifts only its own fog.

    The wall is the one room the player discovers without entering it, so
    it calls ``reveal`` and leaves ``visited`` alone.
    """

    def __init__(self) -> None:
        super().__init__(RoomType.WALL)

    def enter(self, player: Player) -> Outcome:
        self.reveal()
        return Outcome.WALL

    def _revealed_label(self) -> str:
        return "🧱 wall"


class EnemyRoom(Room):
    """The only way onward, and there is no way back.

    Entering is final: the room is revealed at once and the player must
    defeat the enemy to leave it. There is no door out for the gold that
    may sit on the level they just skipped.
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

    def _revealed_label(self) -> str:
        if self.defeated:
            return "⚔️ enemy defeated"
        return "⚔️ enemy"
