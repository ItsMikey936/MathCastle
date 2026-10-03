"""Domain enumerations.

They replace bare strings so that a typo becomes an ``AttributeError``
at import time instead of a silent bug at runtime.
"""

from enum import Enum


class GameState(Enum):
    """Overall state of the run."""

    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_COMBAT = "in_combat"
    VICTORY = "victory"
    DEFEAT = "defeat"


class RoomType(Enum):
    """Kind of room. The player only learns it by entering."""

    GOLD = "gold"
    EMPTY = "empty"
    ENEMY = "enemy"


class Outcome(Enum):
    """Result of a single player action.

    The UI narrates what happened without inspecting engine internals,
    and it can tell apart cases a ``bool`` would merge, such as a wrong
    answer and an expired clock.
    """

    CHALLENGE = "challenge"
    GOLD = "gold"
    NOTHING = "nothing"
    INVALID = "invalid"
    COMBAT_WON = "combat_won"
    COMBAT_LOST = "combat_lost"
    TIMEOUT = "timeout"
    DEFEAT = "defeat"
