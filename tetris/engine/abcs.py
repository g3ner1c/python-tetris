import abc
import random
import secrets
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional, overload

from tetris.types import KickTable
from tetris.types import Minos
from tetris.types import MoveDelta
from tetris.types import PieceType
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
            yield j
            if i >= 7:
                break

    def __contains__(self, x) -> bool:
        return x in self._pieces[:7]

    @overload
    def __getitem__(self, i: int) -> PieceType:
        ...

    @overload
    def __getitem__(self, i: slice) -> list[PieceType]:
        ...

    def __getitem__(self, i):
        if isinstance(i, int):
            return self._pieces[:7][i]

        elif isinstance(i, slice):
            return self._pieces[:7][i]

    def __len__(self) -> int:
        return 7

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self)})"


class Scorer(abc.ABC):
    @abc.abstractmethod
    def judge(self, delta: MoveDelta) -> int:
        ...
