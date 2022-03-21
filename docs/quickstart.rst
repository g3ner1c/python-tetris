Quickstart
==========

This page has a brief introduction to the library. For more in-depth examples, check the
`examples/`_ directory!

.. _examples/: https://github.com/dzshn/python-tetris/tree/main/examples

Installing
----------

This package is available on PyPI::

    pip install tetris
    # or `py -m pip ...` etc.

To install the git version::

    pip install git+https://github.com/dzshn/python-tetris


.. admonition:: todo

    This page..


.. The original section on README.md:

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
