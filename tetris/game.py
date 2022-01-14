import dataclasses
import math
import secrets
from typing import Optional

import numpy as np

from tetris.engine import DefaultEngine
from tetris.engine import Engine
from tetris.types import Board
from tetris.types import DeltaFrame
from tetris.types import Minos
from tetris.types import Move
from tetris.types import MoveType
from tetris.types import Piece
from tetris.types import PieceType
from tetris.types import PlayingStatus


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
        self.queue = engine.queue(seed=self.seed)
        self.scorer = engine.scorer()
        self.score = 0
        self.board = np.zeros((40, 10), dtype=np.int8)
        self.piece = Piece(self.queue.pop(), 18, 3, 0)
        self.status = PlayingStatus.playing
        self.delta = DeltaFrame(None, dataclasses.replace(self.piece))
        self.hold: Optional[PieceType] = None
        self.hold_lock = False

    def reset(self) -> None:
        self.seed = secrets.token_bytes()
        self.queue = self.engine.queue(seed=self.seed)
        self.scorer = self.engine.scorer()
        self.score = 0
        self.board = np.zeros((40, 10), dtype=np.int8)
        self.piece = Piece(self.queue.pop(), 18, 3, 0)
        self.status = PlayingStatus.playing
        self.delta = DeltaFrame(None, dataclasses.replace(self.piece))
        self.hold = None
        self.hold_lock = False

    def _lose(self) -> None:
        self.status = PlayingStatus.stopped

    @property
    def playing(self) -> bool:
        return self.status == PlayingStatus.playing

    @property
    def paused(self) -> bool:
        return self.status == PlayingStatus.idle

    @property
    def lost(self) -> bool:
        return self.status == PlayingStatus.stopped

    def pause(self, state: Optional[bool] = None) -> None:
        if self.status == PlayingStatus.playing and (state is None or state is True):
            self.status = PlayingStatus.idle

        elif self.status == PlayingStatus.idle and (state is None or state is False):
            self.status = PlayingStatus.playing

    def _lock_piece(self) -> None:
        piece = self.piece
        for x in range(piece.x, self.board.shape[0]):
            if _overlaps(self.engine, dataclasses.replace(piece, x=x), self.board):
                break
            piece.x = x

        for x, y in _shape(self.engine, piece):
            self.board[x + piece.x, y + piece.y] = piece.type

        # If all tiles are out of view (half of the internal size), it's a lock-out
        for x, y in _shape(self.engine, piece):
            if self.piece.x + x > self.board.shape[0] / 2:
                break

        else:
            self._lose()

        self.score += self.scorer.judge(self.board, self.delta)

        for i, row in enumerate(self.board):
            if all(row):
                self.board = np.concatenate(  # type: ignore[no-untyped-call]
                    (
                        np.zeros((1, self.board.shape[1]), dtype=np.int8),
                        self.board[:i],
                        self.board[i + 1 :],
                    )
                )

        self.piece.type = self.queue.pop()
        self.piece.x = 18
        self.piece.y = 3
        self.piece.r = 0

        # If the new piece overlaps, it's a block-out
        if _overlaps(self.engine, self.piece, self.board):
            self._lose()

        self.hold_lock = False

    def render(self, tiles: list[str] = list(" ILJSZTO@X"), lines: int = 20) -> str:
        board = self.board.copy()
        piece = self.piece
        ghost = dataclasses.replace(piece)

        for x in range(piece.x, board.shape[0]):
            if _overlaps(self.engine, dataclasses.replace(piece, x=x), board):
                break

            ghost = dataclasses.replace(piece, x=x)

        for x, y in _shape(self.engine, ghost):
            board[x + ghost.x, y + ghost.y] = 8

        for x, y in _shape(self.engine, piece):
            board[x + piece.x, y + piece.y] = piece.type

        return "\n".join("".join(tiles[j] for j in i) for i in board[-lines:])

    def _swap(self) -> None:
        if self.hold_lock:
            return

        if self.hold is None:
            self.hold, self.piece.type = self.piece.type, self.queue.pop()

        else:
            self.hold, self.piece.type = self.piece.type, self.hold

        self.piece.x = 18
        self.piece.y = 3
        self.piece.r = 0
        self.hold_lock = True

    def _move_relative(self, x: int = 0, y: int = 0) -> None:
        self._move(self.piece.x + x, self.piece.y + y)

    def _move(self, x: int = 0, y: int = 0) -> None:
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

        self.delta = DeltaFrame(self.delta.c_piece, dataclasses.replace(piece))

    def _rotate(self, turns: int) -> None:
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

        self.delta = DeltaFrame(self.delta.c_piece, dataclasses.replace(piece))

    def push(self, move: Move) -> None:
        if self.status != PlayingStatus.playing:
            return

        if move.type == MoveType.drag:
            assert move.delta
            self._move_relative(y=move.delta)

        if move.type == MoveType.rotate:
            assert move.delta
            self._rotate(turns=move.delta)

        if move.type == MoveType.drop:
            if move.delta:
                self._move_relative(x=move.delta)

        if move.lock:
            self._lock_piece()

        if move.type == MoveType.swap:
            self._swap()

    def drag(self, tiles: int):
        self.push(Move.drag(tiles))

    def rotate(self, turns: int = 1):
        self.push(Move.rotate(turns))

    def soft_drop(self, tiles: int):
        self.push(Move.soft_drop(tiles))

    def hard_drop(self):
        self.push(Move.hard_drop())

    def swap(self):
        self.push(Move.swap())

    def __str__(self) -> str:
        return self.render(tiles=[i + " " for i in " ILJSZTO@X"])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.engine})"
