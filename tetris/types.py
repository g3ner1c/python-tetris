from __future__ import annotations

import dataclasses
import enum
from typing import final, Optional, TYPE_CHECKING, Union

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from tetris import BaseGame


PieceType = enum.IntEnum("PieceType", "I L J S Z T O")
MoveKind = enum.Enum("MoveKind", "drag rotate soft_drop hard_drop swap")
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


class PartialMove:
    __slots__ = ("kind", "x", "y", "r", "auto")

    def __init__(
        self,
        kind: MoveKind,
        *,
        x: int = 0,
        y: int = 0,
        r: int = 0,
        auto: bool = False,
    ) -> None:
        self.kind = kind
        self.x = x
        self.y = y
        self.r = r % 4
        self.auto = auto


@final
class MoveDelta(PartialMove):
    __slots__ = ("game", "rx", "ry", "rr", "clears")

    def __init__(
        self,
        kind: MoveKind,
        *,
        game: BaseGame,
        x: int = 0,
        y: int = 0,
        r: int = 0,
        clears: Optional[list[int]] = None,
        auto: bool = False,
    ) -> None:
        self.kind = kind
        self.game = game
        self.x = x
        self.y = y
        self.r = r % 4
        self.rx = self.x
        self.ry = self.y
        self.rr = self.r
        self.clears = clears or []
        self.auto = auto


@final
class Move(PartialMove):
    @classmethod
    def drag(cls, tiles: int):
        return cls(MoveKind.drag, y=tiles)

    @classmethod
    def left(cls, tiles: int = 1) -> Move:
        return cls(MoveKind.drag, y=-tiles)

    @classmethod
    def right(cls, tiles: int = 1) -> Move:
        return cls(MoveKind.drag, y=+tiles)

    @classmethod
    def rotate(cls, turns: int = 1) -> Move:
        return cls(MoveKind.rotate, r=turns)

    @classmethod
    def hard_drop(cls) -> Move:
        return cls(MoveKind.hard_drop)

    @classmethod
    def soft_drop(cls, tiles: int = 1) -> Move:
        return cls(MoveKind.soft_drop, x=tiles)

    @classmethod
    def swap(cls) -> Move:
        return cls(MoveKind.swap)
