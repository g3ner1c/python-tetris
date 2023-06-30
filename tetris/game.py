"""Primary implementation for game objects."""

import dataclasses
import math
from collections.abc import Iterable
from typing import Any, Optional, Union

from tetris.board import Board
from tetris.engine import Engine, EngineFactory, Parts
from tetris.impl.presets import Modern
from tetris.types import (
    BoardLike,
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
    factory : tetris.engine.EngineFactory class, optional
        An engine factory object, which builds a mutable engine object for the
        game's core logic. Defaults to using a modern preset.
    rule_overrides : dict[str, Any], optional
        Mapping of rule names to overridden values.

        .. seealso:: `Ruleset`, `Rule`
    board : board_like
        A `tetris.Board` or any compatible type (like a nested sequence, or
        an `object compatible with numpy`__)

        __ https://numpy.org/doc/1.23/user/basics.interoperability.html

        .. hint::
            The *visible* board is half as short as the given (*internal*)
            board. This is so as to "buffer" the board from large attacks.
    level : int, optional
        The initial level to pass to `tetris.engine.Scorer`. Optional, defaults
        to using the `"initial_level"` rule.

        .. hint::
            This is not equivalent to the `"initial_level"` rule, it's meant to
            be used when initialising a game from saved data. Some scorers
            might apply different scoring when the user starts on a different
            level. If that's not your case, use that rule instead of this.
    score : int, default = 0
        The initial score to pass to `tetris.engine.Scorer`.
    queue : Iterable[int], optional
        The initial pieces to pass to `tetris.engine.Queue`.

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
    board : tetris.Board
        The `tetris.Board` storing the board state. All values correspond to
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
        when this is `tetris.PlayingStatus.PLAYING`.

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
        factory: Union[EngineFactory, Parts] = Modern,
        rule_overrides: dict[str, Any] = {},
        /,
        board: Optional[BoardLike] = None,
        queue: Optional[Iterable[int]] = None,
        level: Optional[int] = None,
        score: int = 0,
        seed: Optional[Seed] = None,
        board_size: Optional[tuple[int, int]] = None,
    ):
        if isinstance(factory, EngineFactory):
            self.engine = factory.build()
        else:
            self.engine = Engine(*factory)

        self.rules = Ruleset(
            Rule("board_size", tuple, (20, 10)),
            Rule("initial_level", int, 1),
            Rule("queue_size", int, 4),
            Rule("seed", (int, bytes, str, type(None)), None),
            Rule("can_180_spin", bool, True),
            Rule("can_hard_drop", bool, True),
        )

        if seed is not None:
            self.rules.seed = seed
        if board_size is not None:
            self.rules.board_size = board_size

        if board is None:
            # Internally, we use 2x the height to "buffer" the board being
            # pushed above the view (e.g.: with garbage)
            self.board = Board.zeros(
                (self.rules.board_size[0] * 2, self.rules.board_size[1]),
            )
        elif isinstance(board, Board):
            self.board = board
        else:
            self.board = Board(board)

        if self.board.ndim != 2:
            raise ValueError("board must be 2-dimensional")

        for part in self.engine.parts():
            # Apply overrides from classvars instead of instance attributes, as
            # to avoid rules used within initialization from being ignored.
            if override := getattr(part, "rule_overrides", None):
                self.rules.override(override)

        if level is None:
            level = self.rules.initial_level

        self.gravity = self.engine.gravity.from_game(self)
        self.queue = self.engine.queue.from_game(self, queue)
        self.rs = self.engine.rotation_system.from_game(self)
        self.scorer = self.engine.scorer.from_game(self, score, level)

        for i in (self.gravity, self.queue, self.rs, self.scorer):
            if rules := getattr(i, "rules", None):
                self.rules.register(rules)

        self.rules.override(rule_overrides)  # BaseGame overrides get priority

        self.queue._size = self.rules.queue_size

        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.PLAYING
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
    def seed(self) -> Seed:
        """The random seed being used, shorthand for `queue.seed`."""
        return self.queue.seed

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
        return self.status == PlayingStatus.PLAYING

    @property
    def paused(self) -> bool:
        """True if currently idle (i.e. paused)."""
        return self.status == PlayingStatus.IDLE

    @property
    def lost(self) -> bool:
        """True if the game stopped."""
        return self.status == PlayingStatus.STOPPED

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

        return board[-self.height - buffer_lines :]

    def reset(self) -> None:
        """Restart the game, only keeping the `engine` instance."""
        self.board[:] = 0
        self.gravity = self.engine.gravity.from_game(self)
        self.queue = self.engine.queue.from_game(self)
        self.rs = self.engine.rotation_system.from_game(self)
        self.scorer = self.engine.scorer.from_game(self)
        self.piece = self.rs.spawn(self.queue.pop())
        self.status = PlayingStatus.PLAYING
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
        if self.lost:
            return
        if state or (state is None and self.playing):
            self.status = PlayingStatus.IDLE
        elif state is False or (state is None and self.paused):
            self.status = PlayingStatus.PLAYING

    def _lose(self) -> None:
        self.status = PlayingStatus.STOPPED

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
            self.hold = self.queue.pop()

        self.hold, self.piece = self.piece.type, self.rs.spawn(self.hold)
        self.hold_lock = True
        assert not self.rs.overlaps(self.piece), "piece<-rs.spawn overlaps!"

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
        if turns == 2 and not self.rules.can_180_spin:
            return
        x = self.piece.x
        y = self.piece.y
        r = self.piece.r
        self.rs.rotate(self.piece, turns)
        assert not self.rs.overlaps(self.piece), "rs.rotate overlaps!"
        self.delta.x = x - self.piece.x
        self.delta.y = y - self.piece.y
        self.delta.r = r - self.piece.r

    def push(self, move: PartialMove) -> None:
        """Push a move into the game.

        Parameters
        ----------
        move : tetris.PartialMove
        """
        if self.status != PlayingStatus.PLAYING:
            return

        self.delta = MoveDelta(
            kind=move.kind, game=self, x=move.x, y=move.y, r=move.r, auto=move.auto
        )

        if move.kind == MoveKind.DRAG:
            self._move_relative(y=move.y)

        elif move.kind == MoveKind.ROTATE:
            self._rotate(turns=move.r)

        elif move.kind == MoveKind.SOFT_DROP:
            self._move_relative(x=move.x)

        elif move.kind == MoveKind.SWAP:
            self._swap()

        elif move.kind == MoveKind.HARD_DROP:
            if move.auto or self.rules.can_hard_drop:
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
        return "<%s(EngineFactory(%s), %s, queue=%s, level=%i, score=%i)>" % (
            self.__class__.__name__,
            ", ".join(i.__name__ for i in self.engine.parts()),
            self.rules,
            self.queue,
            self.level,
            self.score,
        )
