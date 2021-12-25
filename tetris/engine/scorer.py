from tetris.engine.abcs import Scorer
from tetris.types import Board
from tetris.types import DeltaFrame
from tetris.types import PieceType


class GuidelineScorer(Scorer):
    def __init__(self):  # type: ignore[no-untyped-def]
        self.level = 1
        self.combo = 0
        self.back_to_back = 0

    def judge(self, board: Board, delta: DeltaFrame) -> int:
        score = 0
        line_clears = sum(all(row) for row in board)
        tspin = False
        tspin_mini = False
        if delta.c_piece.type == PieceType.T and delta.r:
            x = delta.c_piece.x
            y = delta.c_piece.y
            mx, my = board.shape

            # fmt: off
            if x + 2 < mx and x + 2 < my:
                corners = sum(board[(x + 0, x + 2, x + 0, x + 2),
                                    (y + 0, y + 0, y + 2, y + 2)] != 0)
            elif x + 2 > mx and x + 2 < my:
                corners = sum(board[(x + 0, x + 0),
                                    (y + 0, y + 2)] != 0) + 2
            elif y + 2 < my and x + 1 > mx:
                corners = sum(board[(x + 0, x + 2),
                                    (y + 0, y + 0)] != 0) + 2

            if corners >= 3:
                tspin_mini = not (
                    board[[((x + 0, x + 0), (y + 0, y + 2)),
                           ((x + 0, x + 2), (y + 2, y + 2)),
                           ((x + 2, x + 2), (y + 0, y + 2)),
                           ((x + 0, x + 2), (y + 0, y + 0))][delta.c_piece.r]] != 0
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

        return score
