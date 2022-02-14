# python-tetris: a simple and modular tetris library

[![pypi](https://img.shields.io/pypi/v/tetris?logo=python&logoColor=f0f0f0&style=for-the-badge)](https://pypi.org/project/tetris/) | ![versions](https://img.shields.io/pypi/pyversions/tetris?style=for-the-badge) | [![build](https://img.shields.io/github/workflow/status/dzshn/python-tetris/Test%20library?style=for-the-badge)](https://github.com/dzshn/python-tetris/actions/workflows/test.yml) | [![forthebadge](https://forthebadge.com/images/badges/powered-by-black-magic.svg)](https://forthebadge.com) | [![forthebadge](https://forthebadge.com/images/badges/contains-technical-debt.svg)](https://forthebadge.com)

---

## Intro

A simple and modular library for implementing and analysing Tetris games, [guideline](https://archive.org/details/2009-tetris-variant-concepts_202201)-compliant by default

```py
>>> import tetris
>>> game = tetris.BaseGame()
>>> game.engine
Engine(gravity=InfinityGravity, queue=SevenBag, rs=SRS, scorer=GuidelineScorer)
>>> game.queue
SevenBag([PieceType.J, PieceType.O, PieceType.Z, PieceType.I, PieceType.S, PieceType.T, PieceType.S])
>>> print(game)


          @
      @ @ @
```

## Install

This package is available on [PyPI](https://pypi.org/project/tetris/), you can install it with pip:

```sh
pip install tetris

```

Or, build from source using [poetry](https://python-poetry.org/):

```sh
poetry install
poetry build
```

## Quickstart

_For a simple implementation, see [examples/cli.py](https://github.com/dzshn/python-tetris/blob/main/examples/cli.py)_

The main API consists of `tetris.BaseGame` and `tetris.Engine`, which hold the game state and modular implementations respectively

An instance of `tetris.Engine` can be reused between `tetris.BaseGame`s, and contains the subclasses of `Gravity`, `Queue`, `RotationSystem` and `Scorer` that are instantiated within `tetris.BaseGame`. The library provides a default engine (namely `tetris.DefaultEngine`), which parts work roughly akin to modern games

The pseudocode for a standard implementation is the following

```py
import tetris
from tetris import Move

keymap = {
    "a": Move.left(),   # or Move.drag(...)
    "d": Move.right(),
    "w": Move.hard_drop(),
    "s": Move.soft_drop(),
    ... # etc.
}

game = tetris.BaseGame()

while True:
    game.tick()  # Let the library update things like gravity

    render()  # Output the game as you wish
    key = get_key()  # Get current input

    if key in keymap:
        game.push(keymap[key])
```

It's only left to the developer to render and process input
