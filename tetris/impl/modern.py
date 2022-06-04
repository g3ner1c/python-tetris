"""Modern guideline-compliant Tetris implementation."""

from __future__ import annotations

import time
from typing import ClassVar, Final, Optional, TYPE_CHECKING

import tetris
from tetris.types import Minos
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind
from tetris.types import Piece
from tetris.types import PieceType

if TYPE_CHECKING:
    from tetris import BaseGame

from tetris.impl import gravity
from tetris.impl import queue
from tetris.impl import rotation
from tetris.impl import scorer

__all__ = (
    "InfinityGravity",
    "ModernEngine",
    "SevenBag",
    "SRS",
    "Timer",
    "Scorer",
)

KickTable = dict[tuple[int, int], tuple[tuple[int, int], ...]]  # pardon
SECOND: Final[int] = 1_000_000_000  # in nanoseconds


class Timer:
    """Helper class for time-keeping.

    Parameters
    ----------
    seconds : default = 0
    milliseconds : default = 0
    microseconds : default = 0
    nanoseconds : default = 0
    """

    __slots__ = ("duration", "running", "started")

    def __init__(
        self,
        *,
        seconds: float = 0,
        milliseconds: float = 0,
        microseconds: float = 0,
        nanoseconds: float = 0,
    ):
        self.duration = int(
            seconds * 1e9 + milliseconds * 1e6 + microseconds * 1e3 + nanoseconds
        )
        self.started = 0
        self.running = False

    def start(self) -> None:
        """(re)start the timer."""
        self.started = time.monotonic_ns()
        self.running = True

    def stop(self) -> None:
        """Stop the timer."""
        self.started = 0
        self.running = False

    @property
    def done(self) -> bool:
        """True if this timer is running and has finished."""
        return self.running and self.started + self.duration <= time.monotonic_ns()


class InfinityGravity(tetris.engine.Gravity):
    """Marathon gravity with Infinity lock delay.

    Notes
    -----
    See <https://tetris.wiki/Infinity> and <https://tetris.wiki/Marathon>.
    """

    def __init__(self, game: BaseGame):
        self.game = game

        self.idle_lock = Timer(milliseconds=500)
        self.lock_resets = 0
        self.last_drop = time.monotonic_ns()

    def calculate(self, delta: Optional[MoveDelta] = None) -> None:  # noqa: D102
        level = self.game.level
        piece = self.game.piece
        drop_delay = (0.8 - ((level - 1) * 0.007)) ** (level - 1) * SECOND
        now = time.monotonic_ns()

        if delta is not None:
            if delta.kind == MoveKind.hard_drop:
                self.idle_lock.stop()
                self.lock_resets = 0

            if self.idle_lock.running and (delta.x or delta.y or delta.r):
                self.idle_lock.start()
                self.lock_resets += 1

            if not self.idle_lock.running and self.game.rs.overlaps(
                minos=piece.minos, px=piece.x + 1, py=piece.y
            ):
                self.idle_lock.start()

        if self.idle_lock.done or self.lock_resets >= 15:
            self.game.push(Move(kind=MoveKind.hard_drop, auto=True))
            self.idle_lock.stop()
            self.lock_resets = 0

        since_drop = now - self.last_drop
        if since_drop >= drop_delay:
            self.game.push(
                Move(kind=MoveKind.soft_drop, x=int(since_drop / drop_delay), auto=True)
            )
            self.last_drop = now
            if not self.idle_lock.running and self.game.rs.overlaps(
                minos=piece.minos, px=piece.x + 1, py=piece.y
            ):
                self.idle_lock.start()


class SRS(tetris.engine.RotationSystem):
    """The SRS rotation system.

    SRS, aka Super Rotation System or Standard Rotation System, is the rotation
    system found in games following the Tetris Guideline.

    Notes
    -----
    While there are many variations introducing 180° kicks, this class does not
    attempt in doing so. If you wish to use 180° rotation you'll need to extend
    the kick table or use another built-in class like `TetrioSRS`.
    """

    shapes: ClassVar[dict[PieceType, list[Minos]]] = {
        PieceType.I: [
            ((1, 0), (1, 1), (1, 2), (1, 3)),
            ((0, 2), (1, 2), (2, 2), (3, 2)),
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            ((0, 1), (1, 1), (2, 1), (3, 1)),
        ],
        PieceType.L: [
            ((0, 2), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (1, 1), (2, 1), (2, 2)),
            ((1, 0), (1, 1), (1, 2), (2, 0)),
            ((0, 0), (0, 1), (1, 1), (2, 1)),
        ],
        PieceType.J: [
            ((0, 0), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (2, 1)),
            ((1, 0), (1, 1), (1, 2), (2, 2)),
            ((0, 1), (1, 1), (2, 0), (2, 1)),
        ],
        PieceType.S: [
            ((0, 1), (0, 2), (1, 0), (1, 1)),
            ((0, 1), (1, 1), (1, 2), (2, 2)),
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            ((0, 0), (1, 0), (1, 1), (2, 1)),
        ],
        PieceType.Z: [
            ((0, 0), (0, 1), (1, 1), (1, 2)),
            ((0, 2), (1, 1), (1, 2), (2, 1)),
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            ((0, 1), (1, 0), (1, 1), (2, 0)),
        ],
        PieceType.T: [
            ((0, 1), (1, 0), (1, 1), (1, 2)),
            ((0, 1), (1, 1), (1, 2), (2, 1)),
            ((1, 0), (1, 1), (1, 2), (2, 1)),
            ((0, 1), (1, 0), (1, 1), (2, 1)),
        ],
        PieceType.O: [
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
        ],
    }

    kicks: ClassVar[KickTable] = {
        (0, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
        (0, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
        (1, 0): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
        (1, 2): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
        (2, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
        (2, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
        (3, 0): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
        (3, 2): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
    }

    i_kicks: ClassVar[KickTable] = {
        (0, 1): ((+0, -1), (+0, +1), (+1, -2), (-2, +1)),
        (0, 3): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),
        (1, 0): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),
        (1, 2): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),
        (2, 1): ((+0, +1), (+0, -2), (+2, +1), (-1, +2)),
        (2, 3): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),
        (3, 0): ((+0, +1), (+0, -2), (+2, +1), (-1, -2)),
        (3, 2): ((+0, -2), (+0, +1), (+1, -2), (-2, +1)),
    }

    def spawn(self, piece: PieceType) -> Piece:  # noqa: D102
        mx, my = self.board.shape

        return Piece(
            type=piece,
            # just above visible area
            x=mx // 2 - 2,
            # left-aligned centre-ish
            y=(my + 3) // 2 - 3,
            r=0,
            minos=self.shapes[piece][0],
        )

    def rotate(self, piece: Piece, r: int) -> None:  # noqa: D102
        to_r = (piece.r + r) % 4
        minos = self.shapes[piece.type][to_r]

        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            piece.r = to_r

        elif (piece.r, to_r) in self.kicks:
            if piece.type == PieceType.I:
                table = self.i_kicks

            else:
                table = self.kicks

            kicks = table[piece.r, to_r]

            for x, y in kicks:
                if not self.overlaps(minos=minos, px=piece.x + x, py=piece.y + y):
                    piece.x += x
                    piece.y += y
                    piece.r = to_r
                    break

        piece.minos = self.shapes[piece.type][piece.r]


_Tetrio_override = {
    (0, 2): ((-1, +0), (-1, +1), (-1, -1), (+0, +1), (+0, -1)),
    (1, 3): ((+0, +1), (-2, +1), (-1, +1), (-2, +0), (-1, +0)),
    (2, 0): ((+1, +0), (+1, -1), (+1, +1), (+0, -1), (+0, +1)),
    (3, 1): ((+0, -1), (-2, -1), (-1, -1), (-2, +0), (-1, +0)),
}


class Scorer(tetris.engine.Scorer):
    """The Tetris Guideline scoring system.

    Notes
    -----
    Specifically, this class implements the score table defined in the 2009
    guideline with 3 corner T-Spins and T-Spin Mini detection, plus the perfect
    clear score table per recent games.

    A more thorough explanation can be found at <https://tetris.wiki/Scoring>.
    """

    def __init__(self):
        self.score = 0
        self.level = 1
        self.line_clears = 0
        self.combo = 0
        self.back_to_back = 0

    def judge(self, delta: MoveDelta) -> None:  # noqa: D102
        if delta.kind == MoveKind.soft_drop:
            if not delta.auto:
                self.score += delta.x * self.level

        elif delta.kind == MoveKind.hard_drop:
            score = 0

            if not delta.auto:
                score += delta.x * self.level * 2

            piece = delta.game.piece
            board = delta.game.board

            line_clears = len(delta.clears)
            tspin = False
            tspin_mini = False
            if piece.type == PieceType.T and delta.r:
                x = piece.x
                y = piece.y
                mx, my = board.shape

                # fmt: off
                if x + 2 < mx and y + 2 < my:
                    corners = sum(board[(x + 0, x + 2, x + 0, x + 2),
                                        (y + 0, y + 0, y + 2, y + 2)] != 0)
                elif x + 2 > mx and y + 2 < my:
                    corners = sum(board[(x + 0, x + 0),
                                        (y + 0, y + 2)] != 0) + 2
                elif x + 2 < mx and y + 2 > my:
                    corners = sum(board[(x + 0, x + 2),
                                        (y + 0, y + 0)] != 0) + 2

                if corners >= 3:
                    tspin_mini = not (
                        board[[((x + 0, x + 0), (y + 0, y + 2)),
                               ((x + 0, x + 2), (y + 2, y + 2)),
                               ((x + 2, x + 2), (y + 0, y + 2)),
                               ((x + 0, x + 2), (y + 0, y + 0))][piece.r]] != 0
                    ).all() and delta.x < 2

                    tspin = not tspin_mini

                # fmt: on

            if line_clears:
                if tspin or tspin_mini or line_clears >= 4:
                    self.back_to_back += 1
                else:
                    self.back_to_back = 0
                self.combo += 1
            else:
                self.combo = 0

            perfect_clear = all(all(row) or not any(row) for row in board)

            if perfect_clear:
                score += [0, 800, 1200, 1800, 2000][line_clears]

            elif tspin:
                score += [400, 800, 1200, 1600, 0][line_clears]

            elif tspin_mini:
                score += [100, 200, 400, 0, 0][line_clears]

            else:
                score += [0, 100, 300, 500, 800][line_clears]

            if self.combo:
                score += 50 * (self.combo - 1)

            score *= self.level

            if self.back_to_back > 1:
                score = score * 3 // 2
                if perfect_clear:
                    score += 200 * self.level

            self.score += score
            self.line_clears += line_clears
            if line_clears and self.line_clears % 10 == 0:
                self.level += 1


class SevenBag(tetris.engine.Queue):
    """The 7-bag queue randomiser.

    This algorithm is also known as the Random Generator. It was introduced by
    Blue Planet Software and is found in games following the Tetris guideline.

    Notes
    -----
    The algorithm works by creating a "bag" with all the seven tetrominoes and
    shuffling it, then appending it to the queue. Thus, pieces drawn from this
    queue are repeated less often, and it's not possible to have a long run
    without getting a desired piece.
    """

    def fill(self) -> None:  # noqa: D102
        self._pieces.extend(self._random.sample(list(PieceType), 7))


class ModernEngine(tetris.Engine):
    """Guideline-compliant engine implementation."""

    def queue(self, game: BaseGame) -> queue.SevenBag:  # noqa: D102
        return queue.SevenBag(seed=game.seed)

    def scorer(self, game: BaseGame) -> scorer.GuidelineScorer:  # noqa: D102
        return scorer.GuidelineScorer()

    def rotation_system(self, game: BaseGame) -> rotation.SRS:  # noqa: D102
        return rotation.SRS(board=game.board)

    def gravity(self, game: BaseGame) -> gravity.InfinityGravity:  # noqa: D102
        return gravity.InfinityGravity(game=game)
