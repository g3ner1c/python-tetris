import dataclasses
import math
import secrets
from typing import Optional

import numpy as np

from .engine import DefaultEngine
from .engine import Engine
from .types import Board
from .types import Minos
from .types import PieceType


@dataclasses.dataclass
class Piece:
    __slots__ = ("type", "x", "y", "r")

    type: PieceType
    x: int  # = max_x // 2 - 2
    y: int  # = (max_y + 3) // 2 - 3
    r: int  # = 0

    # TODO: figure out where should the defaults above be


def _shape(engine: Engine, piece: Piece) -> Minos:
    return engine.rs.shapes[piece.type][piece.r]


def _overlaps(engine: Engine, piece: Piece, board: Board) -> bool:
    for x, y in _shape(engine, piece):
        x += piece.x
        y += piece.y

        if x not in range(board.shape[0]):
            return True

        if y not in range(board.shape[1]):
            return True

        if board[x, y] != 0:
            return True

    return False


class BaseGame:
    def __init__(self, engine: Engine = DefaultEngine):
        self.engine = engine
        self.seed = secrets.token_bytes()
        self.queue = engine.queue(self.seed)
        self.board = np.zeros((40, 10), dtype=np.int8)
        self.piece = Piece(self.queue.pop(), 18, 3, 0)
        self.hold: Optional[PieceType] = None
        self.hold_lock = False

    def reset(self):
        pass

    def lock_piece(self):
        piece = self.piece
        for x, y in _shape(self.engine, piece):
            self.board[x + piece.x, y + piece.y] = piece.type

        for row, clear in enumerate(self.board.all(1)):
            if clear:
                self.board[row] = 0
                self.board = np.concatenate(
                    (
                        np.roll(self.board[: row + 1], shift=1, axis=0),
                        self.board[row + 1 :],
                    )
                )

        for x, y in _shape(self.engine, piece):
            if x + piece.x < 10:
                self.reset()
                break

        self.piece.type = self.queue.pop()
        self.piece.x = 18
        self.piece.y = 3
        self.piece.r = 0

        if _overlaps(self.engine, self.piece, self.board):
            self.reset()

        self.hold_lock = False

    def render(self, tiles: list[str] = list(" ILJSZTOX@"), lines: int = 20) -> str:
        board = self.board.copy()
        piece = self.piece

        for x in range(piece.x, board.shape[0]):
            if _overlaps(self.engine, dataclasses.replace(piece, x=x), board):
                break

            ghost = dataclasses.replace(piece, x=x)

        for x, y in _shape(self.engine, ghost):
            board[x + ghost.x, y + ghost.y] = 9

        for x, y in _shape(self.engine, piece):
            board[x + piece.x, y + piece.y] = piece.type

        return "\n".join("".join(tiles[j] for j in i) for i in board[-lines:])

    def swap(self):
        if self.hold_lock:
            return

        if self.hold is None:
            self.hold = self.piece.type
            self.piece.type = self.queue.pop()

        else:
            self.hold, self.piece.type = self.piece.type, self.hold
            self.piece.x = 18
            self.piece.y = 3
            self.piece.r = 0

        self.hold_lock = True

    def drag(self, x: int = 0, y: int = 0):
        self.move(self.piece.x + x, self.piece.y + y)

    def move(self, x: int = 0, y: int = 0):
        piece = self.piece
        board = self.board
        from_x = piece.x
        from_y = piece.y

        x_step = int(math.copysign(1, x - from_x))
        for x in range(from_x, x + x_step, x_step):
            if _overlaps(self.engine, dataclasses.replace(piece, x=x), board):
                break
            piece.x = x

        y_step = int(math.copysign(1, y - from_y))
        for y in range(from_y, y + y_step, y_step):
            if _overlaps(self.engine, dataclasses.replace(piece, y=y), board):
                break
            piece.y = y

    def rotate(self, turns: int):
        piece = self.piece
        r = (piece.r + turns) % 4

        kicks = ((+0, +0),) + self.engine.rs.kicks[piece.type][piece.r, r]

        for x, y in kicks:
            if not _overlaps(
                self.engine,
                dataclasses.replace(piece, x=piece.x + x, y=piece.y + y, r=r),
                self.board,
            ):
                piece.x += x
                piece.y += y
                piece.r = r
                break

    def hard_drop(self):
        self.drag(x=self.board.shape[0])
        self.lock_piece()

    def soft_drop(self, height: int = 5):
        self.drag(x=height)
