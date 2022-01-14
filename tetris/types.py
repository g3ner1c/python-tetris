import dataclasses
import enum
from typing import Optional, Union

import numpy as np
from numpy.typing import NDArray

PieceType = enum.IntEnum("PieceType", "I L J S Z T O")
MoveType = enum.Enum("MoveType", "drag rotate drop swap")
PlayingStatus = enum.Enum("PlayingStatus", "playing idle stopped")
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


@dataclasses.dataclass
class Move:
    type: MoveType
    delta: Optional[int] = None
    lock: bool = False

    @classmethod
    def drag(cls, delta: int):
        return cls(MoveType.drag, delta=delta)

    @classmethod
    def left(cls, tiles: int = 1) -> "Move":
        return cls(MoveType.drag, -tiles)

    @classmethod
    def right(cls, tiles: int = 1) -> "Move":
        return cls(MoveType.drag, +tiles)

    @classmethod
    def rotate(cls, turns: int = 1) -> "Move":
        return cls(MoveType.rotate, delta=turns)

    @classmethod
    def hard_drop(cls) -> "Move":
        return cls(MoveType.drop, lock=True)

    @classmethod
    def soft_drop(cls, tiles: int = 1) -> "Move":
        return cls(MoveType.drop, delta=tiles)

    @classmethod
    def swap(cls) -> "Move":
        return cls(MoveType.swap)
