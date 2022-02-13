import dataclasses
import math
import secrets
from typing import Optional

import numpy as np

from tetris.engine import DefaultEngine
from tetris.engine import Engine
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind
from tetris.types import PartialMove
from tetris.types import PieceType
from tetris.types import PlayingStatus

_default_tiles = {
    0: " ",
    PieceType.I: "I",
    PieceType.J: "J",
    PieceType.L: "L",
    PieceType.O: "O",
    PieceType.S: "S",
    PieceType.T: "T",
    PieceType.Z: "Z",
    8: "@",
    9: "X",
}


class BaseGame:
    def __init__(self, engine: Engine = DefaultEngine):
        self.engine = engine
        self.seed = secrets.token_bytes()
        self.board = np.zeros((40, 10), dtype=np.int8)
        self.gravity = engine.gravity(self)
        self.queue = engine.queue(seed=self.seed)
        self.rs = engine.rs(self.board)
        self.scorer = engine.scorer()
        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.playing
        self.delta: Optional[MoveDelta] = None
        self.hold: Optional[PieceType] = None
        self.hold_lock = False

    @property
    def score(self) -> int:
        return self.scorer.score

    @property
    def level(self) -> int:
        return self.scorer.level

    def reset(self) -> None:
        self.seed = secrets.token_bytes()
        self.board = np.zeros((40, 10), dtype=np.int8)
        self.gravity = self.engine.gravity(self)
        self.queue = self.engine.queue(seed=self.seed)
        self.rs = self.engine.rs(self.board)
        self.scorer = self.engine.scorer()
        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.playing
        self.delta = None
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
        assert self.delta
        piece = self.piece
        for x in range(piece.x + 1, self.board.shape[0]):
            if self.rs.overlaps(dataclasses.replace(piece, x=x)):
                break

            piece.x = x
            self.delta.x += 1

        for x, y in piece.minos:
            self.board[x + piece.x, y + piece.y] = piece.type

        # If all tiles are out of view (half of the internal size), it's a lock-out
        for x, y in piece.minos:
            if self.piece.x + x > self.board.shape[0] / 2:
                break

        else:
            self._lose()

        for i, row in enumerate(self.board):
            if all(row):
                self.board[0] = 0
                self.board[1 : i + 1] = self.board[:i]
                self.delta.clears.append(i)

        self.piece = self.rs.spawn(self.queue.pop())

        # If the new piece overlaps, it's a block-out
        if self.rs.overlaps(self.piece):
            self._lose()

        self.hold_lock = False

    def render(self, tiles: dict[int, str] = _default_tiles, lines: int = 20) -> str:
        board = self.board.copy()
        piece = self.piece
        ghost_x = piece.x

        for x in range(piece.x + 1, board.shape[0]):
            if self.rs.overlaps(minos=piece.minos, px=x, py=piece.y):
                break

            ghost_x = x

        for x, y in piece.minos:
            board[x + ghost_x, y + piece.y] = 8
            board[x + piece.x, y + piece.y] = piece.type

        return "\n".join("".join(tiles[j] for j in i) for i in board[-lines:])

    def _swap(self) -> None:
        if self.hold_lock:
            return

        if self.hold is None:
            self.hold, self.piece = self.piece.type, self.rs.spawn(self.queue.pop())

        else:
            self.hold, self.piece = self.piece.type, self.rs.spawn(self.hold)

        self.hold_lock = True

    def _move_relative(self, x: int = 0, y: int = 0) -> None:
        self._move(self.piece.x + x, self.piece.y + y)

    def _move(self, x: int = 0, y: int = 0) -> None:
        assert self.delta
        piece = self.piece
        from_x = piece.x
        from_y = piece.y

        x_step = int(math.copysign(1, x - from_x))
        for x in range(from_x, x + x_step, x_step):
            if self.rs.overlaps(dataclasses.replace(piece, x=x)):
                break

            self.delta.x = x - piece.x
            piece.x = x

        y_step = int(math.copysign(1, y - from_y))
        for y in range(from_y, y + y_step, y_step):
            if self.rs.overlaps(dataclasses.replace(piece, y=y)):
                break

            self.delta.y = y - piece.y
            piece.y = y

    def _rotate(self, turns: int) -> None:
        assert self.delta
        piece = self.piece
        x = piece.x
        y = piece.y
        r = piece.r
        self.rs.rotate(piece, piece.r, (piece.r + turns) % 4)
        self.delta.x = x - self.piece.x
        self.delta.y = y - self.piece.y
        self.delta.r = r - self.piece.r

    def push(self, move: PartialMove) -> None:
        if self.status != PlayingStatus.playing:
            return

        self.delta = MoveDelta(
            kind=move.kind, game=self, x=move.x, y=move.y, r=move.r, auto=move.auto
        )

        if move.kind == MoveKind.drag:
            self._move_relative(y=move.y)

        elif move.kind == MoveKind.rotate:
            self._rotate(turns=move.r)

        elif move.kind == MoveKind.soft_drop:
            self._move_relative(x=move.x)

        elif move.kind == MoveKind.swap:
            self._swap()

        elif move.kind == MoveKind.hard_drop:
            self._lock_piece()

        self.scorer.judge(self.delta)
        if not move.auto:
            self.gravity.calculate(self.delta)

    def tick(self) -> None:
        self.gravity.calculate()

    def drag(self, tiles: int) -> None:
        self.push(Move.drag(tiles))

    def rotate(self, turns: int = 1) -> None:
        self.push(Move.rotate(turns))

    def soft_drop(self, tiles: int) -> None:
        self.push(Move.soft_drop(tiles))

    def hard_drop(self) -> None:
        self.push(Move.hard_drop())

    def swap(self) -> None:
        self.push(Move.swap())

    def __str__(self) -> str:
        return self.render(tiles={k: v + " " for k, v in _default_tiles.items()})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.engine})"
