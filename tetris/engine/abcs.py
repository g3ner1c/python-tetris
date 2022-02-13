from __future__ import annotations

import abc
import random
import secrets
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional, overload, TYPE_CHECKING

from tetris.types import Board
from tetris.types import Minos
from tetris.types import MoveDelta
from tetris.types import Piece
from tetris.types import PieceType
from tetris.types import Seed

if TYPE_CHECKING:
    from tetris import BaseGame


class RotationSystem(abc.ABC):
    def __init__(self, board: Board):
        self.board = board

    @abc.abstractmethod
    def spawn(self, piece: PieceType) -> Piece:
        ...

    @abc.abstractmethod
    def rotate(self, piece: Piece, from_r: int, to_r: int) -> None:
        ...

    @overload
    def overlaps(self, piece: Piece) -> bool:
        ...

    @overload
    def overlaps(self, minos: Minos, px: int, py: int) -> bool:
        ...

    def overlaps(self, piece=None, minos=None, px=None, py=None):
        if piece is not None:
            minos = piece.minos
            px = piece.x
            py = piece.y

        for x, y in minos:
            if x + px not in range(self.board.shape[0]):
                return True

            if y + py not in range(self.board.shape[1]):
                return True

            if self.board[x + px, y + py] != 0:
                return True

        return False


class Queue(abc.ABC, Sequence):
    def __init__(
        self, pieces: Optional[Iterable[int]] = None, seed: Optional[Seed] = None
    ):
        seed = seed or secrets.token_bytes()
        self._seed = seed
        self._random = random.Random(seed)
        self._pieces = [PieceType(i) for i in pieces or []]
        if len(self._pieces) <= 7:
            self.fill()

    def pop(self) -> PieceType:
        if len(self._pieces) <= 7:
            self.fill()

        return self._pieces.pop(0)

    @abc.abstractmethod
    def fill(self) -> None:
        ...

    @property
    def seed(self) -> Seed:
        return self._seed

    def __iter__(self) -> Iterator[PieceType]:
        for i, j in enumerate(self._pieces):
            if i >= 7:
                break
            yield j

    @overload
    def __getitem__(self, i: int) -> PieceType:
        ...

    @overload
    def __getitem__(self, i: slice) -> list[PieceType]:
        ...

    def __getitem__(self, i):
        return self._pieces[:7][i]

    def __len__(self) -> int:
        return 7

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self)})"


class Scorer(abc.ABC):
    score: int
    level: int

    def __init__(self) -> None:
        self.score = 0
        self.level = 1

    @abc.abstractmethod
    def judge(self, delta: MoveDelta) -> None:
        ...


class Gravity(abc.ABC):
    def __init__(self, game: BaseGame):
        self.game = game

    @abc.abstractmethod
    def calculate(self, delta: Optional[MoveDelta] = None) -> None:
        ...
