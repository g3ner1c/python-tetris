import random

from tetris.engine.abcs import Queue
from tetris.types import PieceType
from tetris.types import QueueSeq
from tetris.types import Seed


class SevenBag(Queue):
    def __init__(self, seed: Seed, queue: list[int] = [], bag: list[int] = []):
        self._random = random.Random(seed)
        self._queue = [PieceType(i) for i in queue]
        self._bag = [PieceType(i) for i in bag]
        while len(self._queue) < 4:
            self._queue.append(self._next_piece())

    def _next_piece(self) -> PieceType:
        if not self._bag:
            self._bag = list(PieceType)
            self._random.shuffle(self._bag)

        return self._bag.pop()

    @property
    def pieces(self) -> QueueSeq:
        return self._queue.copy()

    @property
    def bag(self) -> QueueSeq:
        return self._bag.copy()

    def pop(self) -> PieceType:
        piece = self._queue.pop(0)
        self._queue.append(self._next_piece())
        return piece

    def __repr__(self) -> str:
        return f"SevenBag(queue={self.pieces}, bag={self.bag})"


class Chaotic(Queue):
    def __init__(self, seed: Seed):
        self._random = random.Random(seed)
        self._queue = []
        for _ in range(4):
            self._queue.append(PieceType(self._random.randint(1, 7)))

    @property
    def pieces(self) -> QueueSeq:
        return self._queue.copy()

    def pop(self) -> PieceType:
        self._queue.append(PieceType(self._random.randint(1, 7)))
        return self._queue.pop(0)

    def __repr__(self) -> str:
        return "Chaotic()"
