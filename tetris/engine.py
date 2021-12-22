import abc
import dataclasses
import random

from .types import KickTable
from .types import Minos
from .types import PieceType
from .types import QueueSeq
from .types import Seed


class Queue(abc.ABC):
    def __init__(self, seed: Seed):
        ...

    @property
    @abc.abstractmethod
    def pieces(self) -> QueueSeq:
        ...

    @property
    @abc.abstractmethod
    def bag(self) -> QueueSeq:
        ...

    @abc.abstractmethod
    def pop(self) -> PieceType:
        ...

    def __iter__(self) -> QueueSeq:
        yield from self.pieces


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

    def __repr__(self):
        return f"SevenBag(queue={self.pieces}, bag={self.bag})"


class RotationSystem(abc.ABC):
    @property
    @abc.abstractmethod
    def shapes(self) -> dict[PieceType, list[Minos]]:
        ...

    @property
    @abc.abstractmethod
    def kicks(
        self,
    ) -> KickTable:
        ...


class SRS(RotationSystem):
    shapes = {
        PieceType.I: [
            ((1, 0), (1, 1), (1, 2), (1, 3)),
            ((0, 2), (1, 2), (2, 2), (3, 2)),
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            ((0, 1), (1, 1), (2, 1), (3, 1)),
        ],
        PieceType.L: [
            ((0, 2), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (1, 1), (2, 1), (2, 2)),
            ((1, 0), (1, 1), (1, 2), (2, 0)),
            ((0, 0), (0, 1), (1, 1), (2, 1)),
        ],
        PieceType.J: [
            ((0, 0), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (2, 1)),
            ((1, 0), (1, 1), (1, 2), (2, 2)),
            ((0, 1), (1, 1), (2, 0), (2, 1)),
        ],
        PieceType.S: [
            ((0, 1), (0, 2), (1, 0), (1, 1)),
            ((0, 1), (1, 1), (1, 2), (2, 2)),
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            ((0, 0), (1, 0), (1, 1), (2, 1)),
        ],
        PieceType.Z: [
            ((0, 0), (0, 1), (1, 1), (1, 2)),
            ((0, 2), (1, 1), (1, 2), (2, 1)),
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            ((0, 1), (1, 0), (1, 1), (2, 0)),
        ],
        PieceType.T: [
            ((0, 1), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (1, 1), (1, 2), (2, 1)),
            ((1, 0), (1, 1), (1, 2), (2, 1)),
            ((0, 1), (1, 0), (1, 1), (2, 1)),
        ],
        PieceType.O: [
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
        ],
    }

    @property
    def kicks(self) -> KickTable:
        default = {
            (0, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
            (0, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
            (1, 0): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
            (1, 2): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
            (2, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
            (2, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
            (3, 0): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
            (3, 2): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
            # 180 kicks
            (0, 2): (),
            (1, 3): (),
            (2, 0): (),
            (3, 1): (),
        }

        i_kicks = {
            (0, 1): ((+0, -1), (+0, +1), (+1, -2), (-2, +1)),
            (0, 3): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),
            (1, 0): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),
            (1, 2): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),
            (2, 1): ((+0, +1), (+0, -2), (+2, +1), (-1, +2)),
            (2, 3): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),
            (3, 0): ((+0, +1), (+0, -2), (+2, +1), (-1, -2)),
            (3, 2): ((+0, -2), (+0, +1), (+1, -2), (-2, +1)),
        }

        return {
            PieceType.I: default | i_kicks,
            PieceType.L: default,
            PieceType.J: default,
            PieceType.S: default,
            PieceType.Z: default,
            PieceType.T: default,
            PieceType.O: default,
        }


class TetrioSRS(SRS):
    @property
    def kicks(self) -> KickTable:
        override = {
            (0, 2): ((-1, +0), (-1, +1), (-1, -1), (+0, +1), (+0, -1)),
            (1, 3): ((+0, +1), (-2, +1), (-1, +1), (-2, +0), (-1, +0)),
            (2, 0): ((+1, +0), (+1, -1), (+1, +1), (+0, -1), (+0, +1)),
            (3, 1): ((+0, -1), (-2, -1), (-1, -1), (-2, +0), (-1, +0)),
        }

        return {k: v | override for k, v in super().kicks.items()}


@dataclasses.dataclass
class Engine:
    queue: type[Queue]
    rs: RotationSystem


DefaultEngine = Engine(queue=SevenBag, rs=SRS())
