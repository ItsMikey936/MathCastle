"""MathCastle: a math adventure in a castle.

The core lives in this package and imports no UI framework. Presentation
lives in ``ui.py``.
"""

from mathcastle.challenge import Challenge
from mathcastle.constants import (
    ENEMY_DAMAGE_BY_LEVEL,
    GOLD_BY_LEVEL,
    ROOMS_PER_LEVEL,
    STARTING_LIFE_POINTS,
    TIME_LIMIT,
    TOTAL_LEVELS,
)
from mathcastle.enemy import ENEMY_NAMES, Enemy
from mathcastle.enums import GameState, Outcome, RoomType
from mathcastle.game import Game
from mathcastle.level import Level
from mathcastle.player import Player
from mathcastle.problem import MathProblem, ProblemGenerator
from mathcastle.rooms import EmptyRoom, EnemyRoom, GoldRoom, Room, WallRoom

__all__ = [
    "ENEMY_DAMAGE_BY_LEVEL",
    "ENEMY_NAMES",
    "GOLD_BY_LEVEL",
    "ROOMS_PER_LEVEL",
    "STARTING_LIFE_POINTS",
    "TIME_LIMIT",
    "TOTAL_LEVELS",
    "Challenge",
    "EmptyRoom",
    "Enemy",
    "EnemyRoom",
    "Game",
    "GameState",
    "GoldRoom",
    "Level",
    "MathProblem",
    "Outcome",
    "Player",
    "ProblemGenerator",
    "Room",
    "RoomType",
    "WallRoom",
]
