"""Each level is one gold room, one empty room and one enemy."""

import random
from itertools import permutations

from mathcastle.constants import TOTAL_LEVELS
from mathcastle.enums import RoomType
from mathcastle.level import Level
from mathcastle.rooms import GoldRoom

NUMBERS = range(1, TOTAL_LEVELS + 1)


def gold_amount(level: Level) -> int:
    """The gold sitting behind this level's gold room."""
    for room in level.rooms:
        if isinstance(room, GoldRoom):
            return room.gold_amount
    raise AssertionError(f"level {level.number} has no gold room")


def test_every_level_holds_exactly_one_room_of_each_type():
    for number in NUMBERS:
        types = [room.room_type for room in Level(number).rooms]
        assert set(types) == set(RoomType)
        assert len(types) == 3


def test_gold_and_damage_grow_with_the_level():
    assert [gold_amount(Level(n)) for n in NUMBERS] == [10, 20, 30, 40]
    assert [Level(n).enemy_damage for n in NUMBERS] == [2, 3, 4, 5]


def test_the_level_number_drives_its_difficulty():
    assert [Level(n).difficulty for n in NUMBERS] == list(NUMBERS)


def test_the_doors_are_dealt_at_random():
    layouts = set()
    for seed in range(500):
        level = Level(1, rng=random.Random(seed))
        layouts.add(tuple(room.room_type for room in level.rooms))
    assert layouts == set(permutations(RoomType))


def test_get_room_reads_a_door_by_position():
    level = Level(1)
    for index, room in enumerate(level.rooms):
        assert level.get_room(index) is room


def test_all_three_doors_start_open():
    level = Level(1)
    assert level.available_rooms() == [0, 1, 2]


def test_available_rooms_drops_the_doors_already_opened():
    level = Level(1)
    level.get_room(1).mark_visited()
    assert level.available_rooms() == [0, 2]


def test_enemy_room_returns_the_only_enemy():
    level = Level(4)
    assert level.enemy_room() in level.rooms


def test_the_enemy_carries_this_level_damage_and_problem():
    level = Level(4)
    enemy = level.enemy_room().enemy
    assert enemy.damage == level.enemy_damage
    assert enemy.problem.difficulty == 4
    assert eval(enemy.problem.question) == enemy.problem.answer


def test_a_level_knows_how_far_it_has_been_explored():
    level = Level(2)
    assert "visited=0/3" in repr(level)
    level.get_room(0).mark_visited()
    assert "visited=1/3" in repr(level)
