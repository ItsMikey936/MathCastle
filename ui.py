"""Streamlit presentation layer.

This is the only module that imports Streamlit. It draws the game and
calls into :class:`Game`; the engine never calls back here.
"""

from __future__ import annotations

import streamlit as st

from mathcastle.constants import STARTING_LIFE_POINTS, TOTAL_LEVELS
from mathcastle.enums import GameState, Outcome
from mathcastle.game import Game
from mathcastle.level import Level

STATE_KEY = "game"
FEEDBACK_KEY = "feedback"
LOG_KEY = "chronicle"
MAX_LOG_ENTRIES = 25

#: Which Streamlit call narrates each outcome.
_TONES = {
    Outcome.GOLD: "success",
    Outcome.NOTHING: "info",
    Outcome.WALL: "warning",
    Outcome.CHALLENGE: "warning",
    Outcome.INVALID: "warning",
    Outcome.COMBAT_WON: "success",
    Outcome.COMBAT_LOST: "error",
    Outcome.TIMEOUT: "error",
    Outcome.DEFEAT: "error",
}


def _notify(message: str, tone: str) -> None:
    """Stash a message so it survives the rerun that follows an action."""
    st.session_state[FEEDBACK_KEY] = (message, tone)


def _announce(game: Game, outcome: Outcome) -> None:
    """Narrate an outcome and add it to the chronicle."""
    message = game.narrate(outcome)
    _notify(message, _TONES.get(outcome, "info"))
    log = st.session_state[LOG_KEY]
    log.append(message)
    del log[:-MAX_LOG_ENTRIES]


def _reset_transient() -> None:
    """Clear messages and chronicle, keeping the game itself."""
    st.session_state[FEEDBACK_KEY] = None
    st.session_state[LOG_KEY] = []


@st.fragment(run_every=1)
def _countdown(game: Game) -> None:
    """Redraw the countdown every second and enforce the deadline.

    The deadline itself is the engine's business; this fragment only asks
    it to apply the outcome and then refreshes the whole page, because the
    life points and the map live outside the fragment.
    """
    challenge = game.challenge
    if challenge is None:
        return
    st.progress(challenge.fraction_left())
    st.caption(f"Time left: {challenge.remaining():.0f} s")
    outcome = game.tick()
    if outcome is not None:
        _announce(game, outcome)
        st.rerun()


class StreamlitUI:
    """Renders MathCastle and keeps the game in session state."""

    def __init__(self) -> None:
        if STATE_KEY not in st.session_state:
            st.session_state[STATE_KEY] = Game()
            _reset_transient()
        self.game: Game = st.session_state[STATE_KEY]

    def render(self) -> None:
        """Draw whichever screen the current state calls for."""
        st.set_page_config(
            page_title="MathCastle",
            page_icon="🏰",
            layout="wide",
        )
        if self.game.status is GameState.READY:
            self._render_intro()
            return
        self._render_status()
        self._render_feedback()
        self.render_map()
        if self.game.is_over():
            self._render_end()
        elif self.game.status is GameState.IN_COMBAT:
            self.render_challenge()
        else:
            self.render_room_choices()
        self._render_chronicle()
        self._render_new_game_button()

    def render_map(self) -> None:
        """Draw the castle: four levels of four doors each.

        The doors decide what they say. A fogged one shows a question
        mark and nothing more, so the interface never has to know, let
        alone reveal, what is behind a door the player has not opened.
        """
        st.subheader("🗺️ Castle map")
        for level in self.game.levels:
            marker = ""
            if level.number == self.game.current_level:
                marker = "  ← **you are here**"
            st.markdown(f"**Level {level.number}**{marker}")
            for column, index in zip(
                st.columns(len(level.rooms)),
                range(len(level.rooms)),
                strict=True,
            ):
                with column:
                    self._render_door(level, index)

    def render_room_choices(self) -> None:
        """Offer the unopened doors of the current level."""
        st.subheader(f"Level {self.game.current_level}: choose a door")
        st.caption(
            "Behind these doors are one gold room, one empty room, one "
            "wall and one enemy. Only the enemy's door leads onward, and "
            "opening it cannot be undone."
        )

    def render_challenge(self) -> None:
        """Show the running fight: the problem, the clock, the answer box."""
        challenge = self.game.challenge
        if challenge is None:
            return
        enemy = self.game.level().enemy_room().enemy
        st.subheader(f"⚔️ {enemy.name} blocks the way")
        st.caption(
            f"Answer correctly to pass. A wrong answer or an expired clock "
            f"costs {enemy.damage} life points, and you get a new problem."
        )
        st.code(challenge.problem.question)
        _countdown(self.game)
        serial = self.game.challenge_serial
        with st.form(key=f"challenge-{serial}"):
            answer = st.text_input(
                "Your answer",
                key=f"answer-{serial}",
                placeholder="whole number, for example 42",
            )
            submitted = st.form_submit_button("⚔️ Attack", type="primary")
        if submitted:
            self._submit(answer)

    def _render_status(self) -> None:
        """Life points, gold and level, always on screen."""
        player = self.game.player
        life, gold, place = st.columns(3)
        with life:
            st.metric("Level", f"{self.game.current_level} / {TOTAL_LEVELS}")
        with gold:
            st.metric("Gold", player.gold)
        with place:
            st.metric("Life points", f"{player.life_points}")
            st.progress(player.life_points / STARTING_LIFE_POINTS)

    def _render_door(self, level: Level, index: int) -> None:
        """Draw one door, clickable only while it is a real choice."""
        room = level.get_room(index)
        playable = (
            room.is_choosable
            and level.number == self.game.current_level
            and self.game.status is GameState.IN_PROGRESS
        )
        if st.button(
            room.public_label(),
            key=f"door-{level.number}-{index}",
            disabled=not playable,
            width="stretch",
        ):
            self._choose(index)

    def _choose(self, index: int) -> None:
        """Open a door, narrate it, and redraw."""
        try:
            outcome = self.game.choose_room(index)
        except (ValueError, IndexError) as error:
            _notify(str(error), "error")
            st.rerun()
        _announce(self.game, outcome)
        st.rerun()

    def _submit(self, answer: str) -> None:
        """Answer the problem on screen, narrate it, and redraw."""
        try:
            outcome = self.game.submit_answer(answer)
        except ValueError as error:
            _notify(str(error), "error")
            st.rerun()
        _announce(self.game, outcome)
        st.rerun()

    def _render_feedback(self) -> None:
        """Show the message stashed by the last action."""
        stored = None
        if FEEDBACK_KEY in st.session_state:
            stored = st.session_state[FEEDBACK_KEY]
        if not stored:
            return
        message, tone = stored
        getattr(st, tone)(message)

    def _render_intro(self) -> None:
        """The title screen and the rules."""
        st.title("🏰 MathCastle")
        st.write(
            "Four levels deep, three doors on each floor. Behind every set "
            "of doors waits one gold room, one empty room and one enemy."
        )
        st.markdown(
            "- Solve the enemy's problem within **15 seconds** to open the "
            "stairs to the next level.\n"
            "- A wrong answer or an expired clock costs life points, and "
            "every failure brings a brand new problem.\n"
            "- The enemy door is final: you cannot walk back for the gold.\n"
            "- You start with **10 life points**, and the gold you carry out "
            "is your score."
        )
        st.button(
            "Start the adventure",
            key="start",
            type="primary",
            on_click=self._start,
        )

    def _render_end(self) -> None:
        """The closing screen, with the final score."""
        st.subheader("🏆 Victory!" if self.game.is_victory() else "💀 Defeat")
        if self.game.is_victory():
            st.success("You conquered MathCastle and walked out alive.")
        else:
            st.error("The castle keeps you. Your run ends here.")
        score, reached, left = st.columns(3)
        with score:
            st.metric("Final score", f"{self.game.player.gold} gold")
        with reached:
            st.metric("Level reached", self.game.current_level)
        with left:
            st.metric("Life points", self.game.player.life_points)

    def _render_chronicle(self) -> None:
        """Recent events, newest first."""
        log = st.session_state[LOG_KEY]
        if not log:
            return
        with st.expander("Chronicle"):
            for entry in reversed(log):
                st.caption(entry)

    def _render_new_game_button(self) -> None:
        """Always available, so a finished run can be restarted."""
        st.button("New game", on_click=self._new_game)

    def _start(self) -> None:
        """Deal a new castle when the player presses start."""
        st.session_state[STATE_KEY].start_new_game()
        _reset_transient()

    def _new_game(self) -> None:
        """Deal a brand new run, straight onto the castle screen."""
        st.session_state[STATE_KEY].start_new_game()
        _reset_transient()
