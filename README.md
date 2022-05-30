# python-tetris: a simple and modular tetris library

[![pypi](https://img.shields.io/pypi/v/tetris?logo=pypi&logoColor=f0f0f0&style=for-the-badge)](https://pypi.org/project/tetris/)
[![versions](https://img.shields.io/pypi/pyversions/tetris?logo=python&logoColor=f0f0f0&style=for-the-badge)](https://pypi.org/project/tetris/)
[![build](https://img.shields.io/github/workflow/status/dzshn/python-tetris/Test%20library?logo=github&logoColor=f0f0f0&style=for-the-badge)](https://github.com/dzshn/python-tetris/actions/workflows/test.yml)
[![docs](https://img.shields.io/readthedocs/python-tetris?style=for-the-badge)](https://python-tetris.readthedocs.io/en/latest/?badge=latest)
[![technical-debt](https://img.shields.io/badge/contains-technical%20debt-009fef?style=for-the-badge)](https://forthebadge.com/)

---

## Intro

A simple and modular library for implementing and analysing Tetris games, [guideline](https://archive.org/details/2009-tetris-variant-concepts_202201)-compliant by default

```py
>>> import tetris
>>> game = tetris.BaseGame(board_size=(4, 4), seed=128)
>>> game.queue
<SevenBag object [J, O, L, I, T, S, J, ...]>
>>> for _ in range(4): game.hard_drop()
...
>>> game.playing
False
>>> print(game)
J O O
J J J
Z Z
  Z Z
```

## Links

-   [Documentation](https://python-tetris.readthedocs.io/)
-   [PyPI](https://pypi.org/project/tetris)
-   Support: [create an issue](https://github.com/dzshn/python-tetris/issues/new/choose) or [see author contact](https://dzshn.xyz)

## Install

This package is available on [PyPI](https://pypi.org/project/tetris/), you can install it with pip:

```sh
pip install tetris
# or `py -m pip ...` etc.
```

To install the git version:

```sh
pip install git+https://github.com/dzshn/python-tetris
```
