"""Rooms reveal themselves only once entered."""

import pytest

from mathcastle.constants import STARTING_LIFE_POINTS
from mathcastle.enemy import Enemy
from mathcastle.enums import Outcome, RoomType
from mathcastle.player import Player
from mathcastle.problem import MathProblem
from mathcastle.rooms import (
    FOG_LABEL,
    EmptyRoom,
    EnemyRoom,
    GoldRoom,
    Room,
    WallRoom,
)


def make_enemy(damage: int = 3) -> Enemy:
    """An enemy with a trivial problem."""
    return Enemy("Goblin", damage, MathProblem("1 + 1", 2, difficulty=1))


def test_a_gold_room_pays_out_and_is_marked_visited():
    room = GoldRoom(20)
    player = Player()
    assert room.visited is False
    assert room.enter(player) is Outcome.GOLD
    assert player.gold == 20
    assert room.visited is True


def test_a_gold_room_leaves_the_life_points_alone():
    player = Player()
    GoldRoom(20).enter(player)
    assert player.life_points == STARTING_LIFE_POINTS


def test_an_empty_room_does_nothing_at_all():
    room = EmptyRoom()
    player = Player()
    assert room.enter(player) is Outcome.NOTHING
    assert player.gold == 0
    assert player.life_points == STARTING_LIFE_POINTS
    assert room.visited is True


def test_entering_an_enemy_room_only_starts_the_fight():
    room = EnemyRoom(make_enemy())
    player = Player()
    assert room.enter(player) is Outcome.CHALLENGE
    assert room.visited is True
    assert room.defeated is False
    assert player.life_points == STARTING_LIFE_POINTS


def test_defeating_an_enemy_marks_it_and_spares_the_player():
    room = EnemyRoom(make_enemy())
    player = Player()
    room.enter(player)
    assert room.resolve(player, solved=True) is Outcome.COMBAT_WON
    assert room.defeated is True
    assert player.life_points == STARTING_LIFE_POINTS


def test_failing_costs_life_points_and_the_enemy_stays_up():
    room = EnemyRoom(make_enemy(damage=4))
    player = Player()
    room.enter(player)
    assert room.resolve(player, solved=False) is Outcome.COMBAT_LOST
    assert player.life_points == STARTING_LIFE_POINTS - 4
    assert room.defeated is False


def test_life_points_never_dip_below_zero():
    player = Player(life_points=1)
    EnemyRoom(make_enemy(damage=10)).resolve(player, solved=False)
    assert player.life_points == 0
    assert player.is_alive() is False


def test_rooms_carry_their_own_type():
    assert GoldRoom(5).room_type is RoomType.GOLD
    assert EmptyRoom().room_type is RoomType.EMPTY
    assert WallRoom().room_type is RoomType.WALL
    assert EnemyRoom(make_enemy()).room_type is RoomType.ENEMY


def test_the_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Room(RoomType.GOLD)


def test_a_wall_costs_the_player_nothing():
    room = WallRoom()
    player = Player()
    assert room.enter(player) is Outcome.WALL
    assert player.life_points == STARTING_LIFE_POINTS
    assert player.gold == 0


def test_a_wall_is_revealed_but_never_visited():
    room = WallRoom()
    room.enter(Player())
    assert room.revealed is True
    assert room.visited is False


def test_revealing_does_not_count_as_entering():
    room = WallRoom()
    room.reveal()
    assert room.revealed is True
    assert room.visited is False


def test_opening_a_room_also_reveals_it():
    room = EmptyRoom()
    room.enter(Player())
    assert room.revealed is True
    assert room.visited is True


def test_only_a_fogged_door_can_be_chosen():
    room = WallRoom()
    assert room.is_choosable is True
    room.reveal()
    assert room.is_choosable is False


def test_a_fogged_room_shows_the_fog_and_nothing_else():
    assert WallRoom().public_label() == FOG_LABEL


@pytest.mark.parametrize("room_type", list(RoomType))
def test_no_fogged_room_gives_its_type_away(room_type):
    room = {
        RoomType.GOLD: GoldRoom(20),
        RoomType.EMPTY: EmptyRoom(),
        RoomType.WALL: WallRoom(),
        RoomType.ENEMY: EnemyRoom(make_enemy()),
    }[room_type]
    label = room.public_label().lower()
    assert room.public_label() == FOG_LABEL
    assert room_type.value not in label
    assert "gold" not in label


@pytest.mark.parametrize("room_type", list(RoomType))
def test_a_fogged_room_stays_anonymous_in_its_repr(room_type):
    room = {
        RoomType.GOLD: GoldRoom(20),
        RoomType.EMPTY: EmptyRoom(),
        RoomType.WALL: WallRoom(),
        RoomType.ENEMY: EnemyRoom(make_enemy()),
    }[room_type]
    assert repr(room) == "Room(fogged)"
    assert type(room).__name__.lower() not in repr(room).lower()


def test_a_wall_names_itself_once_discovered():
    room = WallRoom()
    room.enter(Player())
    assert room.public_label() == "🧱 wall"
    assert repr(room) == "WallRoom(revealed)"


def test_the_gold_room_names_its_loot_once_opened():
    room = GoldRoom(20)
    room.enter(Player())
    assert room.public_label() == "💰 20 gold"


def test_the_empty_room_names_itself_once_opened():
    room = EmptyRoom()
    room.enter(Player())
    assert room.public_label() == "🫙 empty"


def test_the_enemy_names_itself_and_then_its_defeat():
    room = EnemyRoom(make_enemy())
    room.enter(Player())
    assert room.public_label() == "⚔️ enemy"
    room.resolve(Player(), solved=True)
    assert room.public_label() == "⚔️ enemy defeated"
