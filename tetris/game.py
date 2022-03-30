"""Primary implementation for game objects."""

import dataclasses
import math
import secrets
from typing import Optional

import numpy as np

from tetris.engine import DefaultEngine
from tetris.engine import Engine
from tetris.types import Board
from tetris.types import MinoType
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind
from tetris.types import PartialMove
from tetris.types import PieceType
from tetris.types import PlayingStatus
from tetris.types import Seed

_default_tiles = {
    MinoType.EMPTY: " ",
    MinoType.I: "I",
    MinoType.J: "J",
    MinoType.L: "L",
    MinoType.O: "O",
    MinoType.S: "S",
    MinoType.T: "T",
    MinoType.Z: "Z",
    MinoType.GHOST: "@",
    MinoType.GARBAGE: "X",
}


class BaseGame:
    """Base class for tetris games.

    This class only provides the core game logic and is strictly dependent on
    `tetris.Engine` objects, which provide most of the game logic.

    Parameters
    ----------
    engine : tetris.engine.Engine, default = tetris.DefaultEngine
        An Engine object, which contains the modular logic for the game.
    seed : tetris.types.Seed, optional
        A str, int or bytes object, which will be used as the games's
        random seed. Optional, defaults to calling `secrets.token_bytes`.
    board : tetris.types.Board, optional
        A 2D `numpy.ndarray` with scalar `numpy.int8`, given as the
        initial board data. Optional, defaults to making a new board.

        .. hint::
            The *visible* board is half as short as the given (*internal*)
            board. This is so as to "buffer" the board from large attacks.
    board_size : tuple[int, int], default = (20, 10)
        An integer tuple for the height/width of the (visible) board. This is
        ignored if a board is provided.
    level : int, default = 0
        The inital level to set on `tetris.engine.abcs.Scorer`.
    score : int, default = 0
        The inital score to set on `tetris.engine.abcs.Scorer`.

    Attributes
    ----------
    engine : tetris.Engine
        The `tetris.Engine` instance currently being used by this game.
    board : numpy.ndarray
        The `numpy.ndarray` storing the board state. All values correspond to
        `tetris.MinoType`. This board is twice as tall as the visible board.
        (see `height` and `width` for the proper board shape)

        .. hint::
            This attribute does not include the ghost piece or the
            not-locked piece. Using `render` takes care of this.
    gravity : tetris.engine.abcs.Gravity
        .. seealso:: The `tetris.engine.gravity` module.
    queue : tetris.engine.abcs.Queue
        .. seealso:: The `tetris.engine.queue` module.
    rs: tetris.engine.abcs.RotationSystem
        .. seealso:: The `tetris.engine.rotation` module.
    scorer : tetris.engine.abcs.Scorer
        .. seealso:: The `tetris.engine.scorer` module.
    piece : tetris.Piece
        The active, not-locked piece.
    seed : tetris.types.Seed
        The random seed provided or generated for this game.
    delta : tetris.MoveDelta or None
        The deltas for the last applied move. This is `None` before any move
        is made.
    hold : tetris.PieceType or None
        The hold piece. By default, it starts empty (`None`).
    hold_lock : bool
        True if the hold piece can't be swapped (i.e. it was already swapped).
    status : tetris.PlayingStatus
        Enum referencing the current game status. Pushing moves will only work
        when this is `tetris.PlayingStatus.playing`.

        .. seealso:: `playing`, `paused`, `lost` properties.
    score : int
    level : int
    height : int
    width : int
    playing : bool
    paused : bool
    lost : bool
    """

    def __init__(
        self,
        engine: Engine = DefaultEngine,
        seed: Optional[Seed] = None,
        board: Optional[Board] = None,
        board_size: tuple[int, int] = (20, 10),
        level: int = 0,
        score: int = 0,
    ):
        self.engine = engine
        self.seed = seed or secrets.token_bytes()
        if board is None:
            # Internally, we use 2x the height to "buffer" the board being
            # pushed above the view (e.g.: with garbage)
            self.board = np.zeros((board_size[0] * 2, board_size[1]), dtype=np.int8)

        else:
            self.board = board

        self.gravity = engine.gravity(self)
        self.queue = engine.queue(seed=self.seed)
        self.rs = engine.rs(self.board)

        self.scorer = engine.scorer()
        self.scorer.level = level
        self.scorer.score = score

        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.playing
        self.delta: Optional[MoveDelta] = None
        self.hold: Optional[PieceType] = None
        self.hold_lock = False

    @property
    def score(self) -> int:
        """Current game score, shorthand for `scorer.score`."""
        return self.scorer.score

    @score.setter
    def score(self, value: int) -> None:
        self.scorer.score = value

    @property
    def level(self) -> int:
        """The current game level, shorthand for `scorer.level`."""
        return self.scorer.level

    @level.setter
    def level(self, value: int) -> None:
        self.scorer.level = value

    @property
    def height(self) -> int:
        """The visible board's height. This is half of the internal size."""
        return self.board.shape[0] // 2

    @property
    def width(self) -> int:
        """The visible board's width."""
        return self.board.shape[1]

    @property
    def playing(self) -> bool:
        """True if currently playing."""
        return self.status == PlayingStatus.playing

    @property
    def paused(self) -> bool:
        """True if currently idle (i.e. paused)."""
        return self.status == PlayingStatus.idle

    @property
    def lost(self) -> bool:
        """True if the game stopped."""
        return self.status == PlayingStatus.stopped

    def reset(self, seed: Optional[Seed] = None, level: int = 0) -> None:
        """Restart the game, only keeping the `self.engine` instance.

        Parameters
        ----------
        seed : tetris.types.Seed, optional
            The random seed to initialise this with.
        level : int, optional
            The initial level to set on `tetris.engine.abcs.Scorer`.
        """
        self.seed = seed or secrets.token_bytes()
        self.board[:] = 0
        self.gravity = self.engine.gravity(self)
        self.queue = self.engine.queue(seed=self.seed)
        self.rs = self.engine.rs(self.board)
        self.scorer = self.engine.scorer()
        self.scorer.level = level
        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.playing
        self.delta = None
        self.hold = None
        self.hold_lock = False

    def pause(self, state: Optional[bool] = None) -> None:
        """Pause or resume the game.

        Parameters
        ----------
        state : bool, optional
            If provided, set the pause state to this, otherwise toggle it.
        """
        if self.status == PlayingStatus.playing and (state is None or state is True):
            self.status = PlayingStatus.idle

        elif self.status == PlayingStatus.idle and (state is None or state is False):
            self.status = PlayingStatus.playing

    def _lose(self) -> None:
        self.status = PlayingStatus.stopped

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
            if self.piece.x + x > self.height:
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

    def render(
        self,
        tiles: Optional[dict[MinoType, str]] = None,
        lines: Optional[int] = None,
    ) -> str:
        """Render the `board` to a string.

        This method also takes care of visual clues: the ghost piece and the
        (not locked) piece itself.

        Parameters
        ----------
        tiles : `tetris.MinoType` to str mapping, optional
            A mapping with the corresponding text for the minos.
        lines : int, optional
            Amount of lines to render. Optional, defaults to `height`.

        Returns
        -------
        str
            The rendered board

        Examples
        --------
        >>> ...
        >>> tiles = {i: "[]" for i in tetris.MinoType}
        >>> tiles.update({tetris.MinoType.EMPTY: "  ", tetris.MinoType.GHOST: "@ "})
        >>> print(game.render(tiles=tiles, lines=10))
        <BLANKLINE>
        <BLANKLINE>
        @
        @ @ [][]
        @     [][][]      []
        [][]  [][][][][][][]
        []    [][][][][][][]
        []      [][][][][][]
        [][]  [][][][][][][]
        [][]  [][][][][][][]
        """
        if lines is None:
            lines = self.height

        if tiles is None:
            tiles = _default_tiles

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

    def push(self, move: PartialMove) -> None:
        """Push a move into the game.

        Parameters
        ----------
        move : tetris.PartialMove
        """
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
        """Tick the game's logic."""
        self.gravity.calculate()

    def drag(self, tiles: int) -> None:
        """Shorthand for `push(tetris.Move.drag(tiles))`.

        Parameters
        ----------
        tiles : int
        """
        self.push(Move.drag(tiles))

    def left(self, tiles: int = 1) -> None:
        """Shorthand for `push(tetris.Move.left(tiles))`.

        Parameters
        ----------
        tiles : int
        """
        self.push(Move.left(tiles))

    def right(self, tiles: int = 1) -> None:
        """Shorthand for `push(tetris.Move.right(tiles))`.

        Parameters
        ----------
        tiles : int
        """
        self.push(Move.right(tiles))

    def rotate(self, turns: int = 1) -> None:
        """Shorthand for `push(tetris.Move.rotate(turns))`.

        Parameters
        ----------
        turns : int, default = 1
        """
        self.push(Move.rotate(turns))

    def hard_drop(self) -> None:
        """Shorthand for `push(tetris.Move.hard_drop())`."""
        self.push(Move.hard_drop())

    def soft_drop(self, tiles: int = 1) -> None:
        """Shorthand for `push(tetris.Move.soft_drop(tiles))`.

        Parameters
        ----------
        tiles : int, default = 1
        """
        self.push(Move.soft_drop(tiles))

    def swap(self) -> None:
        """Shorthand for `push(tetris.Move.swap())`."""
        self.push(Move.swap())

    def __str__(self) -> str:
        return self.render(tiles={k: v + " " for k, v in _default_tiles.items()})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.engine})"
