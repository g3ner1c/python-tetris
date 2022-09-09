"""Primary implementation for game objects."""

import dataclasses
import math
import secrets
from collections.abc import Iterable
from typing import Any, Optional

import numpy as np

from tetris.engine import Engine
from tetris.impl.presets import ModernEngine
from tetris.types import (
    Board,
    MinoType,
    Move,
    MoveDelta,
    MoveKind,
    PartialMove,
    PieceType,
    PlayingStatus,
    Rule,
    Ruleset,
    Seed,
)


class BaseGame:
    """Base class for tetris games.

    This class only provides the core game logic and is strictly dependent on
    `tetris.Engine` objects, which provide most of the game logic.

    Parameters
    ----------
    engine : tetris.engine.Engine class, default = tetris.impl.presets.ModernEngine
        An engine class, which contains a game's core logic. The default is to
        mimic a modern Tetris game.
    board : tetris.types.Board, optional
        A 2D `numpy.ndarray` with scalar `numpy.int8`, given as the
        initial board data. Optional, defaults to making a new board.

        .. hint::
            The *visible* board is half as short as the given (*internal*)
            board. This is so as to "buffer" the board from large attacks.
    level : int, optional
        The inital level to pass to `tetris.engine.Scorer`. Optional, defaults
        to using the `"initial_level"` rule.

        .. hint::
            This is not equivalent to the `"initial_level"` rule, it's meant to
            be used when initialising a game from saved data. Some scorers
            might apply different scoring when the user starts on a different
            level. If that's not your case, use that rule instead of this.
    score : int, default = 0
        The inital score to pass to `tetris.engine.Scorer`.
    queue : Iterable[int], optional
        The initial pieces to pass to `tetris.engine.Queue`.
    rule_overrides : dict[str, Any], optional
        Mapping of rule names to overriden values.

        .. seealso:: `Ruleset`, `Rule`
    **options : dict, optional
        Extra arguments to pass to `engine`.

    Other Parameters
    ----------------
    seed : Seed, optional
        Shorthand for updating the `"seed"` rule.
    board_size : tuple[int, int], optional
        Shorthand for updating the `"board_size"` rule.

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
    gravity : tetris.engine.Gravity
    queue : tetris.engine.Queue
    rs: tetris.engine.RotationSystem
    scorer : tetris.engine.Scorer
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
    playfield : Board
    """

    # TODO: Add an examples section on the above.

    def __init__(
        self,
        engine: type[Engine] = ModernEngine,
        /,
        board: Optional[Board] = None,
        queue: Optional[Iterable[int]] = None,
        level: Optional[int] = None,
        score: int = 0,
        seed: Optional[Seed] = None,
        board_size: Optional[tuple[int, int]] = None,
        rule_overrides: dict[str, Any] = {},
        **options: Any,
    ):
        self.engine = engine(**options)

        self.rules = Ruleset(
            Rule("board_size", tuple, (20, 10)),
            Rule("initial_level", int, 1),
            Rule("queue_size", int, 4),
            Rule("seed", (int, bytes, str, type(None)), None),
        )

        if seed:
            self.rules.seed = seed
        if board_size:
            self.rules.board_size = board_size

        if board is None:
            # Internally, we use 2x the height to "buffer" the board being
            # pushed above the view (e.g.: with garbage)
            self.board = np.zeros(
                (self.rules.board_size[0] * 2, self.rules.board_size[1]), dtype=np.int8
            )
        else:
            self.board = board

        self.seed = self.rules.seed or secrets.token_bytes()

        for part in self.engine._get_types():
            # these are all classvars so no need to init
            if override := getattr(part, "rule_overrides", None):
                self.rules.override(override)

            if rules := getattr(part, "rules", None):
                self.rules.register(rules)

        if level is None:
            level = self.rules.initial_level

        self.rules.override(rule_overrides)  # BaseGame overrides get priority

        self.gravity = self.engine.gravity(self)
        self.queue = self.engine.queue(self, queue or [])
        self.rs = self.engine.rotation_system(self)
        self.scorer = self.engine.scorer(self, score=score, level=level)

        self.queue._size = self.rules.queue_size

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

    @property
    def playfield(self) -> Board:
        """The visible board with visual elements."""
        return self.get_playfield(buffer_lines=0)

    def get_playfield(self, buffer_lines: int = 0) -> Board:
        """Return a read-only board with visual elements.

        This function returns the proper playfield, with visual elements
        such as the ghost piece and the current piece. This should be used
        when rendering the game.

        Parameters
        ----------
        buffer_lines : int, default = 0
            By default, the returned board has the dimensions of the visible
            board (see `height`/`width`). This parameter allows you to show
            part of the hidden area.

            .. note::
                If part of the buffer area is shown, it is recommended that
                this area renders out of the board frame.

        Returns
        -------
        Board
            The generated board.
        """
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

        board.flags.writeable = False
        return board[-self.height - buffer_lines :]

    def reset(self) -> None:
        """Restart the game, only keeping the `engine` instance."""
        self.seed = self.rules.seed or secrets.token_bytes()
        self.board[:] = 0
        self.gravity = self.engine.gravity(self)
        self.queue = self.engine.queue(self, [])
        self.rs = self.engine.rotation_system(self)
        self.scorer = self.engine.scorer(self, score=0, level=self.rules.initial_level)
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
        x = self.piece.x
        y = self.piece.y
        r = self.piece.r
        self.rs.rotate(self.piece, turns)
        self.delta.x = x - self.piece.x
        self.delta.y = y - self.piece.y
        self.delta.r = r - self.piece.r

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

        self.queue._size = self.rules.queue_size
        self.queue._safe_fill()
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
        tiles = {
            MinoType.EMPTY: " ",
            MinoType.GHOST: "@",
            MinoType.GARBAGE: "X",
        }

        text = ""
        for line in self.playfield:
            for i in line:
                text += tiles.get(i) or PieceType(i).name
                text += " "
            text += "\n"

        return text.rstrip("\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.engine})"
