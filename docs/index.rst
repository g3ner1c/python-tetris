python-tetris: a simple and modular tetris library
==================================================

.. toctree::
   :hidden:

   quickstart

.. toctree::
   :hidden:
   :caption: API Reference

   tetris <api/tetris>

.. toctree::
   :hidden:
   :caption: Dev

   License <license>

python-tetris is a tetris library for Python, it provides you a clean API to
implement variants of games and to analyse them.

This library only requires `numpy <https://numpy.org>`_ (>= 1.21) and python
itself (>= 3.9).

A quick glance
--------------

.. code:: python

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
