"""Game balance and rules.

Keeping every tunable number in one place means the tests and the
documentation quote the same source of truth.
"""

#: Number of levels in the castle.
TOTAL_LEVELS = 4

#: Doors (rooms) on each level, dealt at random.
ROOMS_PER_LEVEL = 3

#: Life points the player starts with.
STARTING_LIFE_POINTS = 10

#: Seconds allowed to answer each problem, on every level.
TIME_LIMIT = 15

#: Gold hidden in the gold room of each level. The maximum score is 100.
GOLD_BY_LEVEL = {1: 10, 2: 20, 3: 30, 4: 40}

#: Damage the enemy of each level deals when it lands a hit.
ENEMY_DAMAGE_BY_LEVEL = {1: 2, 2: 3, 3: 4, 4: 5}
