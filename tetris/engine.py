"""Basis for core game logic."""

from __future__ import annotations

import abc
import random
import secrets
from collections.abc import Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Any, Optional, overload

from tetris.types import Board, Minos, MoveDelta, Piece, PieceType, Ruleset, Seed

if TYPE_CHECKING:
    from tetris import BaseGame

Self = Any  # Only in 3.11

__all__ = (
    "Engine",
    "Gravity",
    "Queue",
    "RotationSystem",
    "Scorer",
)


class Engine(abc.ABC):
    """Factory object for parts of game logic.

    Notes
    -----
    All methods receive a `BaseGame` as their arguments, this leaves it up to
    the subclass to initialise those. This is useful, for instance, when
    subclassing one of the engine parts and requiring another part of the game
    to be provided (e.g. providing `game.seed`).
    """

    @abc.abstractmethod
    def _get_types(
        self,
    ) -> tuple[type[Gravity], type[Queue], type[RotationSystem], type[Scorer]]:
        """Return the types of the engine parts.

        Returns
        -------
        tuple[type[Gravity], type[Queue], type[RotationSystem], type[Scorer]]
        """
        ...

    @abc.abstractmethod
    def gravity(self, game: BaseGame) -> Gravity:
        """Return a new `Gravity` object.

        Returns
        -------
        Gravity
        """
        ...

    @abc.abstractmethod
    def queue(self, game: BaseGame, pieces: Iterable[int]) -> Queue:
        """Return a new `Queue` object.

        Parameters
        ----------
        pieces : Iterable[int]
            Passed to `Queue`.

        Returns
        -------
        Queue
        """
        ...

    @abc.abstractmethod
    def rotation_system(self, game: BaseGame) -> RotationSystem:
        """Return a new `RotationSystem` object.

        Returns
        -------
        RotationSystem
        """
        ...

    @abc.abstractmethod
    def scorer(self, game: BaseGame, score: int, level: int) -> Scorer:
        """Return a new `Scorer` object.

        Parameters
        ----------
        score : int
            Passed to `Scorer`.
        level : int
            Passed to `Scorer`.

        Returns
        -------
        Scorer
        """
        ...


class EnginePart(abc.ABC):
    """Base API for `Engine` parts.

    Attributes
    ----------
    rules : Ruleset
        Defines rules for this specific object. *Must* have a name set.
    rule_overrides : dict[str, Any]
        Mapping of rule names to overriden values.

    Notes
    -----
    `rules` and `rule_overrides` are optional and may be left undefined, or be
    set to `None`.
    """

    rules: Optional[Ruleset]
    rule_overrides: Optional[dict[str, Any]]

    @classmethod
    @abc.abstractmethod
    def from_game(cls, game: BaseGame) -> Self:
        ...


class Gravity(EnginePart):
    """Abstract base class for gravity implementations.

    Parameters
    ----------
    game : BaseGame
        The game this should operate on.
    """

    def __init__(self, game: BaseGame):
        self.game = game

    @classmethod
    def from_game(cls, game: BaseGame) -> Gravity:
        """Construct this object from a game object."""
        return cls(game=game)

    @abc.abstractmethod
    def calculate(self, delta: Optional[MoveDelta] = None) -> None:
        """Calculate the piece's drop and apply moves.

        This function is called on every `tetris.BaseGame.tick` and
        `tetris.BaseGame.push`. It should take care of timing by itself.

        Parameters
        ----------
        delta : MoveDelta, optional
            The delta, if called from `tetris.BaseGame.push`. This is also not
            provided if the last move was automatic, to prevent recursion.
        """
        ...


class Queue(EnginePart, Sequence):
    """Abstract base class for queue implementations.

    This class extends `collections.abc.Sequence` and consists of `PieceType`
    values.

    Parameters
    ----------
    pieces : Iterable[int], optional
        The pieces to initialise this queue with.
    seed : Seed, optional
        The seed used to generate the pieces. Defaults to
        `secrets.token_bytes()`.

    Notes
    -----
    Although this class is not a `collections.abc.MutableSequence`, it provides
    a `pop` method to remove and return the first piece in the queue, and to
    automatically refill itself if necessary.

    When subclassing, you usually only need to override `fill`. This method
    is expected to unconditionally append at least one `PieceType` to
    `_pieces`. This method will be called when the minimum amount of pieces is
    exhausted (on `BaseGame`, it's by default 4). `_pieces` is a list of
    `PieceType`, and `_random` is a `random.Random` instance using the game's
    seed.

    `RuntimeError` will be raised if `fill` does not increase the length of
    `_pieces`.

    Examples
    --------
    Since most boilerplate is taken care of under the hood, it's really simple
    to subclass this and implement your own queue randomiser. The source code
    for the `SevenBag` class is itself a good example::

        class SevenBag(Queue):
            def fill(self) -> None:
                self._pieces.extend(self._random.sample(list(PieceType), 7))
    """

    def __init__(
        self, pieces: Optional[Iterable[int]] = None, seed: Optional[Seed] = None
    ):
        seed = seed or secrets.token_bytes()
        self._seed = seed
        self._random = random.Random(seed)
        self._pieces = [PieceType(i) for i in pieces or []]
        self._size = 7  # May be changed by a game class
        self._safe_fill()

    def _safe_fill(self):
        prev_size = len(self._pieces)
        while len(self._pieces) <= self._size:
            self.fill()
            if prev_size >= len(self._pieces):
                # Prevent an infinite loop
                raise RuntimeError("fill() did not increase `_pieces`!")

            prev_size = len(self._pieces)

    @classmethod
    def from_game(cls, game: BaseGame, pieces: Optional[Iterable[int]] = None) -> Queue:
        """Construct this object from a game object."""
        return cls(pieces=pieces, seed=game.seed)

    def pop(self) -> PieceType:
        """Remove and return the first piece of the queue."""
        self._safe_fill()
        return self._pieces.pop(0)

    @abc.abstractmethod
    def fill(self) -> None:
        """Refill the queue's pieces.

        Notes
        -----
        Internally, this is called automatically when the queue is exhausted.
        """
        ...

    @property
    def seed(self) -> Seed:
        """The random seed being used."""
        return self._seed

    def __iter__(self) -> Iterator[PieceType]:
        for i, j in enumerate(self._pieces):
            if i >= self._size:
                break
            yield j

    @overload
    def __getitem__(self, i: int) -> PieceType:
        ...

    @overload
    def __getitem__(self, i: slice) -> list[PieceType]:
        ...

    def __getitem__(self, i):
        return self._pieces[: self._size][i]

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} object "
            f"[{', '.join(i.name for i in self) + ', ...'}]>"
        )


class RotationSystem(EnginePart):
    """Abstract base class for rotation systems.

    Parameters
    ----------
    board : tetris.types.Board
        The board this should operate on.
    """

    def __init__(self, board: Board):
        self.board = board

    @classmethod
    def from_game(cls, game: BaseGame) -> RotationSystem:
        """Construct this object from a game object."""
        return cls(board=game.board)

    @abc.abstractmethod
    def spawn(self, piece: PieceType) -> Piece:
        """Return a new piece with a given type.

        Parameters
        ----------
        piece : PieceType
            The piece type to use.

        Returns
        -------
        Piece
            The generated `tetris.Piece` object.
        """
        ...

    @abc.abstractmethod
    def rotate(self, piece: Piece, r: int) -> None:
        """Rotate the given piece in-place.

        Parameters
        ----------
        piece : Piece
            The piece object.
        r : int
            The `r` (rotation) offset.
        """
        ...

    @overload
    def overlaps(self, piece: Piece) -> bool:
        ...

    @overload
    def overlaps(self, minos: Minos, px: int, py: int) -> bool:
        ...

    def overlaps(self, piece=None, minos=None, px=None, py=None):
        """Check if a piece's minos would overlap with anything.

        This method expects either `piece`, or `minos`, `px` and `py` to be
        provided.

        Parameters
        ----------
        piece : tetris.Piece, optional
            The piece object to check against.
        minos : tetris.types.Minos, optional
            The piece's minos to check.
        px : int, optional
            The piece x position.
        py : int, optional
            The piece y position.

        Raises
        ------
        TypeError
            The incorrect arguments were provided.
        """
        if piece is not None:
            minos = piece.minos
            px = piece.x
            py = piece.y

        for x, y in minos:
            if x + px not in range(self.board.shape[0]):
                return True

            if y + py not in range(self.board.shape[1]):
                return True

            if self.board[x + px, y + py] != 0:
                return True

        return False


class Scorer(EnginePart):
    """Abstract base class for score systems.

    Attributes
    ----------
    score : int
        The current game score
    level : int
        The current game level
    """

    score: int
    level: int
    line_clears: int
    goal: int

    def __init__(
        self, score: Optional[int] = None, level: Optional[int] = None
    ) -> None:
        self.score = score or 0
        self.level = level or 1

    @classmethod
    def from_game(
        cls, game: BaseGame, score: Optional[int] = None, level: Optional[int] = None
    ) -> Scorer:
        """Construct this object from a game object."""
        return cls(score=score, level=level)

    @abc.abstractmethod
    def judge(self, delta: MoveDelta) -> None:
        """Judge a game's move.

        Parameters
        ----------
        delta : tetris.MoveDelta
        """
        ...
