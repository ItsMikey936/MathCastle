"""The engine: doors, damage, the deadline, victory and defeat."""

import random

import pytest

from mathcastle.constants import (
    GOLD_BY_LEVEL,
    ROOMS_PER_LEVEL,
    STARTING_LIFE_POINTS,
    TIME_LIMIT,
    TOTAL_LEVELS,
)
from mathcastle.enums import GameState, Outcome, RoomType
from mathcastle.game import Game

WRONG_ANSWER = "-987654"


def new_game(clock=None, seed: int = 0) -> Game:
    """A started game with a clock that never moves on its own."""
    game = Game(rng=random.Random(seed), clock=clock or (lambda: 0.0))
    game.start_new_game()
    return game


def find_door(game: Game, room_type: RoomType) -> int:
    """Position of a room of the given type on the current level."""
    for index, room in enumerate(game.level().rooms):
        if room.room_type is room_type:
            return index
    raise AssertionError(f"no {room_type} room on the current level")


def gold_door(game: Game) -> int:
    """Position of this level's gold room."""
    return find_door(game, RoomType.GOLD)


def enemy_door(game: Game) -> int:
    """Position of this level's enemy room."""
    return find_door(game, RoomType.ENEMY)


def enemy_damage(game: Game) -> int:
    """Damage the enemy on the current level deals."""
    return game.level().enemy_room().enemy.damage


def solve_current_problem(game: Game) -> Outcome:
    """Answer whatever is on screen, correctly."""
    assert game.challenge is not None
    return game.submit_answer(str(game.challenge.problem.answer))


def loot_the_level(game: Game) -> None:
    """Take the gold, then face the enemy."""
    game.choose_room(gold_door(game))
    game.choose_room(enemy_door(game))


def test_a_new_game_starts_at_the_first_level_with_full_health():
    game = new_game()
    assert game.status is GameState.IN_PROGRESS
    assert game.current_level == 1
    assert game.player.life_points == STARTING_LIFE_POINTS
    assert game.player.gold == 0
    assert game.challenge is None


def test_a_new_game_deals_the_whole_castle():
    game = new_game()
    assert len(game.levels) == TOTAL_LEVELS
    assert [level.number for level in game.levels] == [1, 2, 3, 4]


def test_starting_again_throws_the_previous_run_away():
    game = new_game()
    game.choose_room(gold_door(game))
    game.start_new_game()
    assert game.player.gold == 0
    assert game.current_level == 1
    assert game.status is GameState.IN_PROGRESS


def test_opening_a_door_on_an_undealt_game_deals_it_by_itself():
    game = Game(rng=random.Random(3))
    assert game.status is GameState.READY
    game.choose_room(0)
    assert game.status is not GameState.READY
    assert game.status in (GameState.IN_PROGRESS, GameState.IN_COMBAT)
    assert len(game.levels) == TOTAL_LEVELS


def test_the_gold_room_pays_and_leaves_the_player_on_the_same_level():
    game = new_game()
    outcome = game.choose_room(gold_door(game))
    assert outcome is Outcome.GOLD
    assert game.player.gold == GOLD_BY_LEVEL[1]
    assert game.current_level == 1
    assert game.status is GameState.IN_PROGRESS


def test_the_empty_room_changes_nothing():
    game = new_game()
    outcome = game.choose_room(find_door(game, RoomType.EMPTY))
    assert outcome is Outcome.NOTHING
    assert game.player.gold == 0
    assert game.current_level == 1


def test_a_wall_costs_nothing_and_keeps_the_player_on_the_level():
    game = new_game()
    outcome = game.choose_room(find_door(game, RoomType.WALL))
    assert outcome is Outcome.WALL
    assert game.player.life_points == STARTING_LIFE_POINTS
    assert game.player.gold == 0
    assert game.current_level == 1
    assert game.status is GameState.IN_PROGRESS


def test_a_discovered_wall_cannot_be_chosen_again():
    game = new_game()
    index = find_door(game, RoomType.WALL)
    game.choose_room(index)
    assert game.level().get_room(index).revealed is True
    assert game.level().get_room(index).visited is False
    with pytest.raises(ValueError):
        game.choose_room(index)


def test_a_wall_only_lifts_its_own_fog():
    game = new_game()
    level = game.level()
    game.choose_room(find_door(game, RoomType.WALL))
    revealed = [room for room in level.rooms if room.revealed]
    assert len(revealed) == 1
    assert revealed[0].room_type is RoomType.WALL
    assert game.level().available_rooms() == [
        index for index, room in enumerate(level.rooms) if not room.revealed
    ]


def test_a_wall_does_not_stop_the_player_from_reaching_the_next_level():
    game = new_game()
    game.choose_room(find_door(game, RoomType.WALL))
    game.choose_room(enemy_door(game))
    solve_current_problem(game)
    assert game.current_level == 2


def test_the_gold_is_still_reachable_after_finding_the_wall_first():
    game = new_game()
    game.choose_room(find_door(game, RoomType.WALL))
    game.choose_room(gold_door(game))
    assert game.player.gold == GOLD_BY_LEVEL[1]


def test_the_narration_for_a_wall_calls_it_a_dead_end():
    game = new_game()
    outcome = game.choose_room(find_door(game, RoomType.WALL))
    assert "wall" in game.narrate(outcome).lower()


def test_opening_the_enemy_door_starts_the_fight():
    game = new_game()
    outcome = game.choose_room(enemy_door(game))
    assert outcome is Outcome.CHALLENGE
    assert game.status is GameState.IN_COMBAT
    assert game.challenge is not None
    assert game.challenge.problem.difficulty == 1


def test_the_enemy_door_is_final_while_the_fight_is_on():
    game = new_game()
    game.choose_room(enemy_door(game))
    with pytest.raises(ValueError):
        game.choose_room(gold_door(game))


def test_a_door_cannot_be_opened_twice():
    game = new_game()
    index = gold_door(game)
    game.choose_room(index)
    with pytest.raises(ValueError):
        game.choose_room(index)


def test_there_is_no_door_outside_the_four_positions():
    game = new_game()
    for index in (-1, ROOMS_PER_LEVEL, 99):
        with pytest.raises(IndexError):
            game.choose_room(index)


def test_solving_the_problem_defeats_the_enemy_and_opens_the_stairs():
    game = new_game()
    game.choose_room(enemy_door(game))
    assert solve_current_problem(game) is Outcome.COMBAT_WON
    assert game.current_level == 2
    assert game.status is GameState.IN_PROGRESS
    assert game.levels[0].enemy_room().defeated is True
    assert game.level().enemy_room().defeated is False


def test_answering_correctly_costs_no_life_points():
    game = new_game()
    game.choose_room(enemy_door(game))
    solve_current_problem(game)
    assert game.player.life_points == STARTING_LIFE_POINTS


def test_a_wrong_answer_costs_life_points():
    game = new_game()
    game.choose_room(enemy_door(game))
    damage = enemy_damage(game)
    assert game.submit_answer(WRONG_ANSWER) is Outcome.COMBAT_LOST
    assert game.player.life_points == STARTING_LIFE_POINTS - damage


def test_a_wrong_answer_serves_a_brand_new_problem():
    game = new_game()
    game.choose_room(enemy_door(game))
    first = game.challenge.problem
    serial = game.challenge_serial
    game.submit_answer(WRONG_ANSWER)
    assert game.challenge.problem is not first
    assert game.challenge_serial > serial


def test_the_new_problem_keeps_the_level_difficulty():
    game = new_game()
    loot_the_level(game)
    game.submit_answer(WRONG_ANSWER)
    assert game.challenge.problem.difficulty == 1


def test_a_wrong_answer_does_not_unlock_the_doors():
    game = new_game()
    game.choose_room(enemy_door(game))
    game.submit_answer(WRONG_ANSWER)
    assert game.status is GameState.IN_COMBAT
    with pytest.raises(ValueError):
        game.choose_room(gold_door(game))


def test_the_player_can_still_win_after_a_wrong_answer():
    game = new_game()
    game.choose_room(enemy_door(game))
    game.submit_answer(WRONG_ANSWER)
    solve_current_problem(game)
    assert game.current_level == 2
    assert game.is_victory() is False


def test_nonsense_input_is_rejected_without_punishment():
    game = new_game()
    game.choose_room(enemy_door(game))
    problem = game.challenge.problem
    assert game.submit_answer("banana") is Outcome.INVALID
    assert game.submit_answer("") is Outcome.INVALID
    assert game.submit_answer("4.5") is Outcome.INVALID
    assert game.player.life_points == STARTING_LIFE_POINTS
    assert game.challenge.problem is problem


def test_surrounding_spaces_do_not_break_a_valid_answer():
    game = new_game()
    game.choose_room(enemy_door(game))
    answer = str(game.challenge.problem.answer)
    assert game.submit_answer(f"  {answer}  ") is Outcome.COMBAT_WON


def test_an_answer_after_the_deadline_counts_as_wrong(clock):
    game = new_game(clock)
    game.choose_room(enemy_door(game))
    damage = enemy_damage(game)
    clock.advance(TIME_LIMIT)
    answer = str(game.challenge.problem.answer)
    assert game.submit_answer(answer) is Outcome.TIMEOUT
    assert game.player.life_points == STARTING_LIFE_POINTS - damage


def test_a_tick_before_the_deadline_changes_nothing(clock):
    game = new_game(clock)
    game.choose_room(enemy_door(game))
    problem = game.challenge.problem
    clock.advance(TIME_LIMIT - 1)
    assert game.tick() is None
    assert game.challenge.problem is problem
    assert game.player.life_points == STARTING_LIFE_POINTS


def test_a_tick_after_the_deadline_applies_the_damage(clock):
    game = new_game(clock)
    game.choose_room(enemy_door(game))
    damage = enemy_damage(game)
    clock.advance(TIME_LIMIT)
    assert game.tick() is Outcome.TIMEOUT
    assert game.player.life_points == STARTING_LIFE_POINTS - damage
    assert game.status is GameState.IN_COMBAT


def test_an_expired_problem_is_replaced_after_a_timeout(clock):
    game = new_game(clock)
    game.choose_room(enemy_door(game))
    first = game.challenge.problem
    clock.advance(TIME_LIMIT)
    game.tick()
    assert game.challenge.problem is not first


def test_ticking_outside_a_fight_does_nothing():
    game = new_game()
    assert game.tick() is None


def test_there_is_no_problem_to_answer_outside_a_fight():
    game = new_game()
    with pytest.raises(ValueError):
        game.submit_answer("1")


def test_running_out_of_life_points_ends_the_run():
    game = new_game()
    game.choose_room(enemy_door(game))
    for _ in range(20):
        if game.is_over():
            break
        game.submit_answer(WRONG_ANSWER)
    assert game.status is GameState.DEFEAT
    assert game.player.life_points == 0
    assert game.is_victory() is False
    assert game.is_over() is True


def test_a_dead_player_cannot_keep_playing():
    game = new_game()
    game.choose_room(enemy_door(game))
    while not game.is_over():
        game.submit_answer(WRONG_ANSWER)
    with pytest.raises(ValueError):
        game.choose_room(0)
    with pytest.raises(ValueError):
        game.submit_answer("1")


def test_a_player_who_always_fails_dies_on_the_first_level():
    game = new_game(seed=2)
    for _ in range(100):
        if game.is_over():
            break
        if game.status is GameState.IN_COMBAT:
            game.submit_answer(WRONG_ANSWER)
        else:
            game.choose_room(enemy_door(game))
    assert game.status is GameState.DEFEAT
    assert game.current_level == 1


def test_defeating_the_last_enemy_wins_the_game():
    game = new_game(seed=11)
    while not game.is_over():
        loot_the_level(game)
        solve_current_problem(game)
    assert game.status is GameState.VICTORY
    assert game.is_victory() is True
    assert game.current_level == TOTAL_LEVELS


def test_a_clean_run_collects_every_gold_coin():
    game = new_game(seed=7)
    while not game.is_over():
        loot_the_level(game)
        solve_current_problem(game)
    assert game.player.gold == sum(GOLD_BY_LEVEL.values())
    assert game.player.life_points == STARTING_LIFE_POINTS


def test_advance_level_stops_at_the_bottom_of_the_castle():
    game = new_game()
    for _ in range(TOTAL_LEVELS * 3):
        game.advance_level()
    assert game.current_level == TOTAL_LEVELS


def test_every_outcome_produced_by_a_run_can_be_narrated():
    game = new_game(seed=4)
    game.choose_room(gold_door(game))
    assert game.narrate(Outcome.GOLD)
    game.choose_room(enemy_door(game))
    assert game.narrate(Outcome.CHALLENGE)
    assert game.narrate(game.submit_answer("banana")) is not None
    assert game.narrate(game.submit_answer(WRONG_ANSWER))
    assert game.narrate(solve_current_problem(game))


def test_the_narration_says_how_much_gold_was_found():
    game = new_game()
    outcome = game.choose_room(gold_door(game))
    assert str(GOLD_BY_LEVEL[1]) in game.narrate(outcome)


def test_the_narration_reports_the_damage_that_was_taken():
    game = new_game()
    game.choose_room(enemy_door(game))
    outcome = game.submit_answer(WRONG_ANSWER)
    narration = game.narrate(outcome)
    assert str(enemy_damage(game)) in narration
    assert str(game.player.life_points) in narration


def test_the_narration_for_a_timeout_says_the_clock_ran_out(clock):
    game = new_game(clock)
    game.choose_room(enemy_door(game))
    clock.advance(TIME_LIMIT)
    assert "Time is up" in game.narrate(game.tick())


def test_the_narration_for_a_defeat_reports_the_final_score():
    game = new_game()
    game.choose_room(gold_door(game))
    game.choose_room(enemy_door(game))
    while not game.is_over():
        game.submit_answer(WRONG_ANSWER)
    assert str(game.player.gold) in game.narrate(Outcome.DEFEAT)
