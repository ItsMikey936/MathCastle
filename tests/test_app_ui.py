"""The Streamlit layer, driven headlessly through AppTest.

These tests exercise the real widgets: the same buttons, forms and
feedback a player touches in the browser.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from mathcastle.constants import (
    GOLD_BY_LEVEL,
    ROOMS_PER_LEVEL,
    TIME_LIMIT,
    TOTAL_LEVELS,
)
from mathcastle.enums import GameState, RoomType
from mathcastle.game import Game

APP = str(Path(__file__).resolve().parents[1] / "app.py")
WRONG_ANSWER = "-987654"


def launch(clock=None) -> AppTest:
    """A running app, optionally with a clock the test owns."""
    app = AppTest.from_file(APP, default_timeout=30)
    if clock is not None:
        app.session_state["game"] = Game(clock=clock)
    app.run()
    return app


def started(clock=None) -> AppTest:
    """A running app with the castle already dealt."""
    app = launch(clock)
    app.button(key="start").click().run()
    return app


def game_of(app: AppTest) -> Game:
    """The engine behind the running app."""
    return app.session_state["game"]


def door_of_type(app: AppTest, level: int, room_type: RoomType) -> int:
    """Which door on a level hides a room of the given type."""
    rooms = game_of(app).levels[level - 1].rooms
    for index, room in enumerate(rooms):
        if room.room_type is room_type:
            return index
    raise AssertionError(f"no {room_type} room on level {level}")


def submitters(app: AppTest) -> list:
    """The submit buttons that belong to a form."""
    return [
        button
        for button in app.button
        if str(button.key).startswith("FormSubmitter")
    ]


def labels(app: AppTest) -> list[str]:
    """Every door label on the map."""
    return [
        button.label
        for button in app.button
        if str(button.key).startswith("door-")
    ]


def rendered(app: AppTest) -> str:
    """Every scrap of text the app currently shows the player."""
    parts: list[str] = []
    for group in (
        app.title,
        app.subheader,
        app.markdown,
        app.caption,
        app.code,
        app.success,
        app.error,
        app.warning,
        app.info,
    ):
        parts.extend(item.value for item in group)
    parts.extend(metric.value for metric in app.metric)
    parts.extend(button.label for button in app.button)
    return " ".join(parts)


def answer_current_problem(app: AppTest, raw: str) -> None:
    """Type into the answer box and press Attack."""
    serial = game_of(app).challenge_serial
    app.text_input(key=f"answer-{serial}").set_value(raw)
    submitters(app)[0].click().run()


def solve(app: AppTest) -> None:
    """Beat whatever enemy is on screen."""
    challenge = game_of(app).challenge
    assert challenge is not None
    answer_current_problem(app, str(challenge.problem.answer))


def play_level(app: AppTest, level: int) -> None:
    """Loot a level and defeat its enemy."""
    gold = door_of_type(app, level, RoomType.GOLD)
    app.button(key=f"door-{level}-{gold}").click().run()
    enemy = door_of_type(app, level, RoomType.ENEMY)
    app.button(key=f"door-{level}-{enemy}").click().run()
    solve(app)


def test_the_title_screen_explains_the_rules():
    app = launch()
    assert app.title[0].value == "🏰 MathCastle"
    assert app.button(key="start").label == "Start the adventure"
    assert "15 seconds" in app.markdown[-1].value


def test_the_castle_is_not_dealt_before_the_player_starts():
    app = launch()
    assert game_of(app).status is GameState.READY
    assert not labels(app)


def test_starting_shows_the_map_the_hud_and_four_closed_doors():
    app = started()
    assert [header.value for header in app.subheader][:2] == [
        "🗺️ Castle map",
        "Level 1: choose a door",
    ]
    assert len(labels(app)) == TOTAL_LEVELS * ROOMS_PER_LEVEL
    assert set(labels(app)) == {"🚪 ?"}


def test_the_hud_reports_the_level_the_gold_and_the_life_points():
    app = started()
    assert [(m.label, m.value) for m in app.metric] == [
        ("Level", f"1 / {TOTAL_LEVELS}"),
        ("Gold", "0"),
        ("Life points", "10"),
    ]


def test_only_the_doors_of_the_current_level_can_be_opened():
    app = started()
    enabled = {
        button.key for button in app.button if not button.disabled
    }
    assert enabled == {"door-1-0", "door-1-1", "door-1-2", "door-1-3", None}


def test_a_closed_door_never_leaks_what_is_behind_it():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    shown = labels(app)
    assert shown.count("🚪 ?") == TOTAL_LEVELS * ROOMS_PER_LEVEL - 1
    assert "⚔️ enemy" in shown
    assert "gold" not in " ".join(shown)


def test_the_map_never_shows_the_layout_of_the_unexplored():
    app = started()
    secret = f"{GOLD_BY_LEVEL[1]} gold"
    assert secret not in rendered(app)
    assert set(labels(app)) == {"🚪 ?"}


def test_finding_a_wall_still_says_nothing_about_the_gold():
    app = started()
    secret = f"{GOLD_BY_LEVEL[1]} gold"
    wall = door_of_type(app, 1, RoomType.WALL)
    app.button(key=f"door-1-{wall}").click().run()
    assert secret not in rendered(app)
    assert labels(app).count("🚪 ?") == TOTAL_LEVELS * ROOMS_PER_LEVEL - 1
    assert labels(app).count("🧱 wall") == 1


def test_a_discovered_wall_shows_itself_and_shuts_for_good():
    app = started()
    wall = door_of_type(app, 1, RoomType.WALL)
    app.button(key=f"door-1-{wall}").click().run()
    assert "🧱 wall" in labels(app)
    assert app.button(key=f"door-1-{wall}").disabled is True
    assert "wall" in app.warning[-1].value.lower()


def test_a_wall_costs_no_life_points_and_no_gold():
    app = started()
    wall = door_of_type(app, 1, RoomType.WALL)
    app.button(key=f"door-1-{wall}").click().run()
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Gold"] == "0"
    assert metrics["Life points"] == "10"
    assert game_of(app).current_level == 1


def test_the_rest_of_the_level_is_still_playable_after_a_wall():
    app = started()
    wall = door_of_type(app, 1, RoomType.WALL)
    app.button(key=f"door-1-{wall}").click().run()
    gold = door_of_type(app, 1, RoomType.GOLD)
    app.button(key=f"door-1-{gold}").click().run()
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Gold"] == str(GOLD_BY_LEVEL[1])


def test_a_whole_castle_run_walks_into_every_wall_and_still_wins():
    app = started()
    for level in range(1, TOTAL_LEVELS + 1):
        wall = door_of_type(app, level, RoomType.WALL)
        app.button(key=f"door-{level}-{wall}").click().run()
        play_level(app, level)
    assert game_of(app).is_victory() is True
    assert ("Final score", "100 gold") in [
        (m.label, m.value) for m in app.metric
    ]


def test_opening_the_gold_room_updates_the_hud_and_the_map():
    app = started()
    index = door_of_type(app, 1, RoomType.GOLD)
    app.button(key=f"door-1-{index}").click().run()
    assert ("Gold", str(GOLD_BY_LEVEL[1])) in [
        (m.label, m.value) for m in app.metric
    ]
    assert f"💰 {GOLD_BY_LEVEL[1]} gold" in labels(app)
    assert app.success[0].value.startswith("You find")


def test_an_opened_door_can_no_longer_be_chosen():
    app = started()
    index = door_of_type(app, 1, RoomType.EMPTY)
    app.button(key=f"door-1-{index}").click().run()
    assert app.button(key=f"door-1-{index}").disabled is True


def test_opening_the_enemy_door_shows_the_problem():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    challenge = game_of(app).challenge
    assert app.code[0].value == challenge.problem.question
    assert app.text_input
    assert submitters(app)
    assert any("Time left" in caption.value for caption in app.caption)


def test_no_door_is_open_while_the_fight_is_on():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    assert all(button.disabled for button in app.button
               if str(button.key).startswith("door-"))


def test_answering_correctly_moves_the_player_down_a_level():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    solve(app)
    assert game_of(app).current_level == 2
    assert ("Level", f"2 / {TOTAL_LEVELS}") in [
        (m.label, m.value) for m in app.metric
    ]
    assert "defeat" in app.success[-1].value


def test_nonsense_costs_nothing_and_keeps_the_same_problem():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    problem = game_of(app).challenge.problem
    answer_current_problem(app, "banana")
    assert game_of(app).challenge.problem is problem
    assert ("Life points", "10") in [
        (m.label, m.value) for m in app.metric
    ]
    assert "whole number" in app.warning[-1].value


def test_a_wrong_answer_costs_life_points_and_clears_the_box():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    answer_current_problem(app, WRONG_ANSWER)
    assert ("Life points", "8") in [(m.label, m.value) for m in app.metric]
    assert app.error[-1].value.startswith("Wrong!")
    assert game_of(app).challenge_serial == 2
    assert app.text_input[0].value == ""


def test_the_clock_running_out_ends_the_attempt():
    clock = FakeClock()
    app = started(clock)
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    clock.advance(TIME_LIMIT)
    app.run()
    assert ("Life points", "8") in [(m.label, m.value) for m in app.metric]
    assert "Time is up" in app.error[-1].value


def test_a_whole_castle_run_ends_in_victory():
    app = started()
    for level in range(1, TOTAL_LEVELS + 1):
        play_level(app, level)
    assert game_of(app).is_victory() is True
    assert ("Final score", "100 gold") in [
        (m.label, m.value) for m in app.metric
    ]
    assert app.subheader[-1].value == "🏆 Victory!"


def test_a_whole_castle_run_can_end_in_defeat():
    app = started()
    index = door_of_type(app, 1, RoomType.ENEMY)
    app.button(key=f"door-1-{index}").click().run()
    for _ in range(20):
        if game_of(app).is_over():
            break
        answer_current_problem(app, WRONG_ANSWER)
    assert game_of(app).is_victory() is False
    assert app.subheader[-1].value == "💀 Defeat"


def test_the_new_game_button_starts_a_clean_run():
    app = started()
    play_level(app, 1)
    restart = [
        button
        for button in app.button
        if button.key is None and "New game" in button.label
    ]
    restart[0].click().run()
    assert game_of(app).status is GameState.IN_PROGRESS
    assert ("Gold", "0") in [(m.label, m.value) for m in app.metric]
    assert ("Life points", "10") in [(m.label, m.value) for m in app.metric]
    assert set(labels(app)) == {"🚪 ?"}


def test_the_chronicle_records_what_happened():
    app = started()
    index = door_of_type(app, 1, RoomType.GOLD)
    app.button(key=f"door-1-{index}").click().run()
    assert app.expander[0].label == "Chronicle"
    assert game_of(app).player.gold > 0


@pytest.mark.parametrize("level", range(1, TOTAL_LEVELS + 1))
def test_every_level_can_be_reached_through_the_ui(level):
    app = started()
    for reached in range(1, level):
        play_level(app, reached)
    assert game_of(app).current_level == level
    assert set(labels(app)) >= {"🚪 ?"}


class FakeClock:
    """A clock that only moves when a test tells it to."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
