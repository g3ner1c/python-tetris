from typing import ClassVar

from tetris.engine.abcs import RotationSystem
from tetris.types import Minos
from tetris.types import Piece
from tetris.types import PieceType

KickTable = dict[tuple[int, int], tuple[tuple[int, int], ...]]  # pardon


class SRS(RotationSystem):
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

    def spawn(self, piece: PieceType) -> Piece:
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

    def rotate(self, piece: Piece, from_r: int, to_r: int) -> None:
        minos = self.shapes[piece.type][to_r]

        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            piece.r = to_r

        elif (from_r, to_r) in self.kicks:
            if piece.type == PieceType.I:
                table = self.i_kicks

            else:
                table = self.kicks

            kicks = table[from_r, to_r]

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


class TetrioSRS(SRS):
    kicks: ClassVar[KickTable] = SRS.kicks | _Tetrio_override
    i_kicks: ClassVar[KickTable] = SRS.i_kicks | _Tetrio_override


class NoKicks(SRS):
    kicks: ClassVar[KickTable] = {}
    i_kicks: ClassVar[KickTable] = {}
