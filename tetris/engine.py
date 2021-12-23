import abc
import dataclasses
import random
from collections.abc import Iterator

from .types import Board
from .types import DeltaFrame
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

    def __iter__(self) -> Iterator[PieceType]:
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

    def __repr__(self) -> str:
        return f"SevenBag(queue={self.pieces}, bag={self.bag})"


class RotationSystem(abc.ABC):
    @property
    @abc.abstractmethod
    def shapes(self) -> dict[PieceType, list[Minos]]:
        ...

    @property
    @abc.abstractmethod
    def kicks(self) -> KickTable:
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


class Scorer(abc.ABC):
    @abc.abstractmethod
    def judge(self, board: Board, delta: DeltaFrame) -> int:
        ...


class GuidelineScorer(Scorer):
    def __init__(self):  # type: ignore[no-untyped-def]
        self.level = 1
        self.combo = 0
        self.back_to_back = 0

    def judge(self, board: Board, delta: DeltaFrame) -> int:
        score = 0
        line_clears = sum(all(row) for row in board)
        tspin = False
        tspin_mini = False
        if delta.c_piece.type == PieceType.T and delta.r:
            x = delta.c_piece.x
            y = delta.c_piece.y
            mx, my = board.shape

            # fmt: off
            if x + 2 < mx and x + 2 < my:
                corners = sum(board[(x + 0, x + 2, x + 0, x + 2),
                                    (y + 0, y + 0, y + 2, y + 2)] != 0)
            elif x + 2 > mx and x + 2 < my:
                corners = sum(board[(x + 0, x + 0),
                                    (y + 0, y + 2)] != 0) + 2
            elif y + 2 < my and x + 1 > mx:
                corners = sum(board[(x + 0, x + 2),
                                    (y + 0, y + 0)] != 0) + 2

            if corners >= 3:
                tspin_mini = not (
                    board[[((x + 0, x + 0), (y + 0, y + 2)),
                           ((x + 0, x + 2), (y + 2, y + 2)),
                           ((x + 2, x + 2), (y + 0, y + 2)),
                           ((x + 0, x + 2), (y + 0, y + 0))][delta.c_piece.r]] != 0
                ).all() and delta.x < 2

                tspin = not tspin_mini

            # fmt: on

        if line_clears:
            if tspin or tspin_mini or line_clears >= 4:
                self.back_to_back += 1
            else:
                self.back_to_back = 0
            self.combo += 1
        else:
            self.combo = 0

        perfect_clear = all(all(row) or not any(row) for row in board)

        if perfect_clear:
            score += [0, 800, 1200, 1800, 2000][line_clears]

        elif tspin:
            score += [400, 800, 1200, 1600, 0][line_clears]

        elif tspin_mini:
            score += [100, 200, 400, 0, 0][line_clears]

        else:
            score += [0, 100, 300, 500, 800][line_clears]

        if self.combo:
            score += 50 * (self.combo - 1)

        score *= self.level

        if self.back_to_back > 1:
            score = score * 3 // 2
            if perfect_clear:
                score += 200 * self.level

        return score


@dataclasses.dataclass
class Engine:
    queue: type[Queue]
    rs: RotationSystem
    scorer: type[Scorer]


DefaultEngine = Engine(queue=SevenBag, rs=SRS(), scorer=GuidelineScorer)
