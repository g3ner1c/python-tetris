import abc
from collections.abc import Iterator

from tetris.types import Board
from tetris.types import DeltaFrame
from tetris.types import KickTable
from tetris.types import Minos
from tetris.types import PieceType
from tetris.types import QueueSeq
from tetris.types import Seed


class RotationSystem(abc.ABC):
    @property
    @abc.abstractmethod
    def shapes(self) -> dict[PieceType, list[Minos]]:
        ...

    @property
    @abc.abstractmethod
    def kicks(self) -> KickTable:
        ...


class Queue(abc.ABC):
    def __init__(self, seed: Seed):
        ...

    @property
    @abc.abstractmethod
    def pieces(self) -> QueueSeq:
        ...

    @abc.abstractmethod
    def pop(self) -> PieceType:
        ...

    def __iter__(self) -> Iterator[PieceType]:
        yield from self.pieces


class Scorer(abc.ABC):
    @abc.abstractmethod
    def judge(self, board: Board, delta: DeltaFrame) -> int:
        ...
