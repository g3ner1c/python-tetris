"""Collection of scoring systems."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from tetris.engine import Scorer
from tetris.types import MoveDelta, MoveKind, PieceType

if TYPE_CHECKING:
    from tetris.game import BaseGame


class GuidelineScorer(Scorer):
    """The Tetris Guideline scoring system.

    Notes
    -----
    Specifically, this class implements the score table defined in the 2009
    guideline with 3 corner T-Spins and T-Spin Mini detection, plus the perfect
    clear score table per recent games.

    A more thorough explanation can be found at <https://tetris.wiki/Scoring>.
    """

    def __init__(self, score: Optional[int] = None, level: Optional[int] = None):
        self.score = score or 0
        self.level = level or 1
        self.line_clears = 0
        self.goal = self.level * 10
        self.combo = 0
        self.back_to_back = 0
        self.tspin = False
        self.tspin_mini = False

    def judge(self, delta: MoveDelta) -> None:  # noqa: D102
        piece = delta.game.piece
        board = delta.game.board

        self.tspin = False
        self.tspin_mini = False

        # useful: https://tetris.wiki/T-Spin#Current_rules
        if delta.kind == MoveKind.ROTATE and piece.type == PieceType.T and delta.r != 0:
            px = piece.x
            py = piece.y
            corners = []
            # check corners clockwise from top-left
            for x, y in [(0, 0), (0, 2), (2, 2), (2, 0)]:
                corners.append(
                    x + px not in range(board.shape[0])
                    or y + py not in range(board.shape[1])
                    or board[x + px, y + py] != 0
                )

            back = None
            # find the back of the piece clockwise from top. note how this
            # is checked in the same order as the corners: corners[back] will
            # be the corner before the back edge (behind counter-clockwise)
            for i, pos in enumerate([(0, 1), (1, 2), (2, 1), (1, 0)]):
                if pos not in piece.minos:
                    back = i
                    break

            # ideally, an edge is always found. unless:
            #  - the piece's center is not 1,1 (should this be checked?)
            #  - its not T-shaped
            if back is not None:
                front_corners = corners[(back + 2) % 4] + corners[(back + 3) % 4]
                back_corners = corners[(back + 0) % 4] + corners[(back + 1) % 4]
                # if there are two corners in the front edge..
                if front_corners == 2 and back_corners >= 1:
                    # it's a proper t-spin!
                    self.tspin = True
                # but, if there is one corner in front edge and two in the back..
                elif front_corners == 1 and back_corners == 2:
                    # this is still a tspin!
                    if abs(delta.x) == 2 and abs(delta.y) == 1:
                        # the piece was kicked far, proper t-spin!
                        self.tspin = True
                    else:
                        # last case, mini-tspin
                        self.tspin_mini = True

        if delta.kind == MoveKind.SOFT_DROP:  # soft drop
            if not delta.auto:
                self.score += delta.x

        elif delta.kind == MoveKind.HARD_DROP:  # hard drop
            score = 0

            if not delta.auto:  # not done by gravity
                self.score += delta.x * 2
                # self.score instead because hard drop isn't affected by level

            line_clears = len(delta.clears)  # how many lines cleared

            if line_clears:  # B2B and combo
                if self.tspin or self.tspin_mini or line_clears >= 4:
                    self.back_to_back += 1
                else:
                    self.back_to_back = 0
                self.combo += 1
            else:
                self.combo = 0

            perfect_clear = all(not any(row) for row in board)

            if perfect_clear:
                score += [0, 800, 1200, 1800, 2000][line_clears]

            elif self.tspin:
                score += [400, 800, 1200, 1600, 0][line_clears]

            elif self.tspin_mini:
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

            if self.line_clears >= self.goal:
                self.goal += 10
                self.level += 1


class NESScorer(Scorer):
    """The NES scoring system.

    Notes
    -----
    This class implements the original scoring system found in the Nintendo NES
    Tetris games.

    A more thorough explanation can be found at <https://tetris.wiki/Scoring>.
    """

    rule_overrides = {"initial_level": 0}

    def __init__(
        self,
        score: Optional[int] = None,
        level: Optional[int] = None,
        initial_level: Optional[int] = None,
    ) -> None:
        self.score = score or 0
        self.level = level or 0  # NES starts on level 0
        self.line_clears = 0
        self.initial_level = initial_level or 0
        self.goal = min(
            self.initial_level * 10 + 10, max(100, self.initial_level * 10 - 50)
        )

    @classmethod
    def from_game(
        cls,
        game: BaseGame,
        score: Optional[int] = None,
        level: Optional[int] = None,
    ) -> NESScorer:  # noqa: D102
        return cls(score=score, level=level, initial_level=game.rules.initial_level)

    def judge(self, delta: MoveDelta) -> None:  # noqa: D102
        if delta.kind == MoveKind.SOFT_DROP:
            if not delta.auto:
                self.score += delta.x

        elif delta.kind == MoveKind.HARD_DROP:
            # NRS doesn't have hard drop score bonus but added anyways for
            # compatibility and modularity with other rotation systems
            if not delta.auto:
                self.score += delta.x
            score = 0
            line_clears = len(delta.clears)

            score += [0, 40, 100, 300, 1200][line_clears]
            score *= self.level + 1

            self.score += score
            self.line_clears += line_clears
            if self.line_clears >= self.goal:
                self.level += 1
                self.goal = self.line_clears + 10
