"""Collection of queue implementations."""

from __future__ import annotations

from tetris.engine import Queue
from tetris.types import PieceType


class SevenBag(Queue):
    """The 7-bag queue randomiser.

    This algorithm is also known as the Random Generator. It was introduced by
    Blue Planet Software and is found in games following the Tetris guideline.

    Notes
    -----
    The algorithm works by creating a "bag" with all the seven tetrominoes and
    shuffling it, then appending it to the queue. Thus, pieces drawn from this
    queue are repeated less often, and it's not possible to have a long run
    without getting a desired piece.
    """

    def fill(self) -> None:  # noqa: D102
        self._pieces.extend(self._random.sample(list(PieceType), 7))
