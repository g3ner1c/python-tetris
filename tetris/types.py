from __future__ import annotations

import dataclasses
import enum
from collections.abc import Iterable
from typing import final, Optional, TYPE_CHECKING, Union

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from tetris import BaseGame


MoveKind = enum.Enum("MoveKind", "drag rotate soft_drop hard_drop swap")
PlayingStatus = enum.Enum("PlayingStatus", "playing idle stopped")
Board = NDArray[np.int8]
Minos = Iterable[tuple[int, int]]
Seed = Union[str, bytes, int]


class PieceType(enum.IntEnum):
    I = enum.auto()  # noqa
    J = enum.auto()
    L = enum.auto()
    O = enum.auto()  # noqa
    S = enum.auto()
    T = enum.auto()
    Z = enum.auto()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@dataclasses.dataclass
class Piece:
    __slots__ = ("type", "x", "y", "r", "minos")

    type: PieceType
    x: int
    y: int
    r: int
    minos: Minos


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
    def drag(cls, tiles: int) -> Move:
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
