# MathCastle

A single-player math adventure that runs in the browser. You go down four
levels of a castle, opening one of three doors on each floor. One door
holds gold, one is empty and one hides an enemy. Only the enemy's door
opens the stairs to the next level, and it cannot be undone.

The enemy asks one math problem with a 15 second clock. Solve it to pass.
Get it wrong, or let the clock run out, and the enemy lands a hit. Every
failure costs life points and brings a brand new problem, so a losing
streak is survivable right up until it is not.

You start with 10 life points. Your score is the gold you carry out.

## Running it

```bash
uv sync                 # create .venv and install streamlit + pytest
uv run streamlit run app.py
```

Then open the URL Streamlit prints, normally http://localhost:8501.

## Running the tests

```bash
uv run pytest                      # 104 tests
uv run pytest tests/test_game.py   # just the engine
uv run pytest -k timeout           # just the clock behaviour
```

The suite covers the engine directly and drives the real widgets through
`streamlit.testing.v1.AppTest`, so the buttons, forms and countdown are
tested without a browser. The deadline tests use an injected fake clock, so
nothing ever sleeps.

## How it is laid out

Game logic and presentation are strictly separated: no module inside
`mathcastle/` imports Streamlit, and `ui.py` is the only file that does.

| File | Role |
| --- | --- |
| `app.py` | Entry point, three lines long. |
| `ui.py` | `StreamlitUI`: the map, the HUD, the countdown, the forms. |
| `mathcastle/enums.py` | `GameState`, `RoomType`, `Outcome`. |
| `mathcastle/constants.py` | Every tunable number in one place. |
| `mathcastle/player.py` | Life points and gold. |
| `mathcastle/problem.py` | `MathProblem` and `ProblemGenerator`. |
| `mathcastle/challenge.py` | A countdown on an injectable clock. |
| `mathcastle/enemy.py` | Name, damage and problem of a guard. |
| `mathcastle/rooms.py` | `Room` and its three subclasses. |
| `mathcastle/level.py` | Three doors dealt at random. |
| `mathcastle/game.py` | The engine: doors, damage, victory, defeat. |

## Balance

| Level | Enemy damage | Gold |
| --- | --- | --- |
| 1 | 2 | 10 |
| 2 | 3 | 20 |
| 3 | 4 | 30 |
| 4 | 5 | 40 |

Life points start at 10 and the clock is 15 seconds on every level. The
maximum score is 100. Failing on all four levels would cost 14 life
points, more than you have, so you cannot simply spam wrong answers.

Problems get harder as you descend: single digit sums on level 1,
multiplication and two digit arithmetic on level 2, exact division, squares
and parentheses on level 3, two step expressions with negative results on
level 4. They are generated, never hardcoded, and the test suite verifies
every answer by evaluating its own question.

## Design notes

- **The clock lives in the engine.** `Challenge` holds the deadline over an
  injectable clock, so the 15 second rule is enforced by the game rather
  than by the interface. The UI only asks `Game.tick()` whether the time
  ran out.
- **Outcomes, not booleans.** `Room.enter` returns an `Outcome`, which lets
  the interface narrate gold, an empty room, a wrong answer and an expired
  clock as four different things instead of two.
- **A wrong answer changes the problem.** This is what keeps the enemy room
  from being a soft lock: you are already committed to the fight, and the
  only way out is to beat it.
- **A non numeric answer is free.** Typing nonsense is rejected without
  costing life points, so the clock keeps running instead of punishing a
  typo twice.
- **Closed doors leak nothing.** Unopened doors are identical question marks
  on the map. Once opened, they reveal what was behind them. Note that when
  only one door is left on a level, the enemy can be deduced by elimination;
  that is inherent to the rules, not an oversight.