"""Levels: three doors dealt at random, one of each type."""

from __future__ import annotations

import random

from mathcastle.constants import ENEMY_DAMAGE_BY_LEVEL, GOLD_BY_LEVEL
from mathcastle.enemy import ENEMY_NAMES, Enemy
from mathcastle.enums import RoomType
from mathcastle.problem import ProblemGenerator
from mathcastle.rooms import EmptyRoom, EnemyRoom, GoldRoom, Room


class Level:
    """One floor of the castle: one gold room, one empty room, one enemy."""

    def __init__(
        self,
        number: int,
        generator: ProblemGenerator | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.number = number
        self.difficulty = number
        self.enemy_damage = ENEMY_DAMAGE_BY_LEVEL[number]
        source: random.Random = rng if rng is not None else random
        self._generator = generator or ProblemGenerator()
        self._rooms = self._build_rooms(source)

    def _build_rooms(self, source: random.Random) -> list[Room]:
        """Deal the three room types at random and build each one."""
        types = list(RoomType)
        source.shuffle(types)
        rooms: list[Room] = []
        for room_type in types:
            if room_type is RoomType.GOLD:
                rooms.append(GoldRoom(GOLD_BY_LEVEL[self.number]))
            elif room_type is RoomType.EMPTY:
                rooms.append(EmptyRoom())
            else:
                rooms.append(self._build_enemy(source))
        return rooms

    def _build_enemy(self, source: random.Random) -> EnemyRoom:
        """Build this level's enemy with its first problem."""
        name = source.choice(list(ENEMY_NAMES))
        problem = self._generator.generate(self.difficulty, source)
        return EnemyRoom(Enemy(name, self.enemy_damage, problem))

    @property
    def rooms(self) -> tuple[Room, ...]:
        """The rooms, in the fixed order their doors were dealt."""
        return tuple(self._rooms)

    def get_room(self, index: int) -> Room:
        """Return the room behind a door position."""
        return self._rooms[index]

    def available_rooms(self) -> list[int]:
        """Door positions that have not been entered yet."""
        return [
            index
            for index, room in enumerate(self._rooms)
            if not room.visited
        ]

    def enemy_room(self) -> EnemyRoom:
        """This level's enemy room.

        Raises LookupError only if the level was built without one, which
        the dealing rules make impossible.
        """
        for room in self._rooms:
            if isinstance(room, EnemyRoom):
                return room
        raise LookupError(f"level {self.number} has no enemy room")

    def __repr__(self) -> str:
        visited = sum(room.visited for room in self._rooms)
        return f"Level({self.number}, visited={visited}/3)"
