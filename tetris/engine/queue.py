"""Built-in queue implementations."""

from tetris.engine.abcs import Queue
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


class Chaotic(Queue):
    """Completely random queue randomiser.

    This does not provide any protection against piece repetition.
    """

    def fill(self) -> None:  # noqa: D102
        while len(self._pieces) < 7:
            self._pieces.append(PieceType(self._random.randint(1, 7)))
