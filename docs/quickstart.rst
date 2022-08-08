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

What an implementation might look like
-------------------------------------
This library allows for quick and lightweight implementations of tetris games.
The following pseudocode shows a basic implementation of the game:

.. code:: python

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
        game.tick()  # let the library update things like gravity

        render()  # output the game as you wish
        key = get_key()  # get current input

        if key in keymap:
            game.push(keymap[key])

It's only left to the developer to render and process input.

See `examples/cli.py`_, for a ``curses`` implementation.

.. _examples/cli.py: https://github.com/dzshn/python-tetris/blob/main/examples/cli.py

Initializing a new game instance
--------------------------------

.. code:: python

     >>> import tetris
     >>> game = tetris.BaseGame()

``BaseGame`` is the base class for all game instances, provides core Tetris logic shared
across different Tetris implementations. It uses a ``tetris.Engine`` object for modular
game logic and by default uses ``tetris.impl.presets.ModernEngine``, a modern
implementation that adheres to `guideline Tetris rules`_ including SRS and 7-Bag.

An instance of ``tetris.Engine`` can be reused between multiple ``BaseGame`` instances,
and contains the subclasses of ``Gravity``, ``Queue``, ``RotationSystem`` and ``Scorer``
which each provide the logic for their respective mechanics.

.. _guideline Tetris rules: https://archive.org/details/2009-tetris-variant-concepts_202201

Rendering a game
----------------

.. code:: python

     >>> game.playfield
     array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [6, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [6, 6, 0, 0, 0, 0, 0, 0, 0, 0],
            [6, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [8, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [8, 8, 3, 3, 0, 0, 0, 0, 0, 0],
            [8, 0, 0, 3, 0, 0, 5, 5, 0, 1],
            [2, 2, 0, 3, 6, 5, 5, 4, 4, 1],
            [2, 0, 0, 6, 6, 6, 1, 4, 4, 1],
            [2, 0, 0, 0, 5, 5, 1, 7, 7, 1],
            [4, 4, 0, 5, 5, 3, 1, 2, 7, 7],
            [4, 4, 0, 3, 3, 3, 1, 2, 2, 2]], dtype=int8)

The ``playfield`` attribute returns a 2D array of the current state of the visible
board with each value representing the state of a single cell that can be used to
render a user interface.

.. note::
    Arrays representing the board are top-to-bottom, left-to-right, 0-indexed. This is
    different from the usual convention of coordinates being left-to-right,
    bottom-to-top, 1-indexed.
    
    For example the cell that is 1 above and 1 to the right of the bottom-left cell
    is ``game.playfield[18, 1]`` instead of ``game.playfield[2, 2]``, assuming a board
    shape of ``(20, 10)``.

Each ``int8`` value corresponds to a `tetris.MinoType` enum memeber:
 ======= ===========
  int8    MinoType
 ======= ===========
  0       EMPTY
  1       I
  2       J
  3       L
  4       O
  5       S
  6       T
  7       Z
  8       GHOST
  9       GARBAGE
 ======= ===========

A one-liner can be used to output the array as a minimal game board:

.. code:: python

     >>> print('\n'.join([''.join(['[]' if cell in range(1, 8) else '@ ' if cell == 8 else 'X ' if cell == 9 else '  ' for cell in row]) for row in game.playfield]))
                         
                         
                         
                         
                         
                         
                         
                         
                         
     []                  
     [][]                
     []                  
                         
                         
     @                   
     @ @ [][]            
     @     []    [][]  []
     [][]  [][][][][][][]
     []    [][][][][][][]
     []      [][][][][][]
     [][]  [][][][][][][]
     [][]  [][][][][][][]

Alternatively, simply printing the ``BaseGame`` object will output letters representing
each cell.

.. code:: python

     >>> print(game)
                             
                         
                         
                         
                         
                         
                         
     T                   
     T T                 
     T                   
                         
                         
     @                   
     @ @ L L             
     @     L     S S   I 
     J J   L T S S O O I 
     J     T T T I O O I 
     J       S S I Z Z I 
     O O   S S L I J Z Z 
     O O   L L L I J J J 

Pushing moves to the engine
---------------------------

Moves can be sent to the engine by calling ``BaseGame.push()`` with a ``tetris.Move``
object.

.. code:: python

     >>> from tetris import Move
     >>> game.push(Move.left())
     >>> game.push(Move.right())
     >>> game.push(Move.rotate())
     >>> game.push(Move.hard_drop())
     >>> game.push(Move.soft_drop())
     >>> game.push(Move.swap())

However, you can also call direct methods of ``BaseGame`` instead that are equivalent to
calling ``push()`` with ``tetris.Move``.

.. code:: python

     >>> game.left()
     >>> game.right()
     >>> game.rotate()
     >>> game.hard_drop()
     >>> game.soft_drop()
     >>> game.swap()

Ticking gravity
---------------

Calling ``BaseGame.tick()`` will update the game state according to gravity and the
amount of time that has passed since the last tick. To have a responsive game, you
should call ``tick()`` at least once per frame inside a game loop.

.. code:: python

    import tetris
    game = tetris.BaseGame()
    print(f"{chr(27)}[2J", end="") # clear screen
    while True:
        print(f"{chr(27)}[;H", end="") # move cursor to top-left
        game.tick() # update the game state
        print('\n'.join( # one-liner to render game 😎
            [''.join([
                '[]' if cell in range(1, 8)
                    else '@ ' if cell == 8
                    else 'X ' if cell == 9
                    else '  ' for cell in row]) for row in game.playfield]))

        # input stuff, etc.
        # should probably just use curses tbh
