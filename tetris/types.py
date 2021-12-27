import dataclasses
import enum
from typing import Optional, Union

import numpy as np
from numpy.typing import NDArray

PieceType = enum.IntEnum("PieceType", "I L J S Z T O")
Board = NDArray[np.int8]
KickTable = dict[PieceType, dict[tuple[int, int], tuple[tuple[int, int], ...]]]
Minos = tuple[tuple[int, int], ...]
Seed = Union[str, bytes, int]


@dataclasses.dataclass
class Piece:
    __slots__ = ("type", "x", "y", "r")

    type: PieceType
    x: int  # = max_x // 2 - 2
    y: int  # = (max_y + 3) // 2 - 3
    r: int  # = 0

    # TODO: figure out where should the defaults above be


@dataclasses.dataclass(frozen=True)
class DeltaFrame:
    __slots__ = ("p_piece", "c_piece")

    p_piece: Optional[Piece]
    c_piece: Piece

    @property
    def x(self) -> int:
        if self.p_piece is None:
            return self.c_piece.x

        return self.c_piece.x - self.p_piece.x

    @property
    def y(self) -> int:
        if self.p_piece is None:
            return self.c_piece.y

        return self.c_piece.y - self.p_piece.y

    @property
    def r(self) -> int:
        if self.p_piece is None:
            return self.c_piece.r

        return (self.c_piece.r - self.p_piece.r) % 4
