from tetris.engine.abcs import Queue
from tetris.types import PieceType


class SevenBag(Queue):
    def fill(self) -> None:
        self._pieces.extend(self._random.sample(list(PieceType), 7))


class Chaotic(Queue):
    def fill(self) -> None:
        while len(self._pieces) < 7:
            self._pieces.append(PieceType(self._random.randint(1, 7)))
