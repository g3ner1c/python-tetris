from tetris.engine.abcs import RotationSystem
from tetris.types import Piece
from tetris.types import PieceType


class SRS(RotationSystem):
    shapes = {
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

    kicks = {
        (0, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
        (0, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
        (1, 0): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
        (1, 2): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),
        (2, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),
        (2, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),
        (3, 0): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
        (3, 2): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),
    }

    i_kicks = {
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

    def rotate(self, piece: Piece, from_r: int, to_r: int):
        minos = self.shapes[piece.type][to_r]

        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            piece.r = to_r

        elif (from_r, to_r) in self.kicks:
            if piece.type == PieceType.I:
                table = self.kicks | self.i_kicks

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


class TetrioSRS(SRS):
    _override = {
        (0, 2): ((-1, +0), (-1, +1), (-1, -1), (+0, +1), (+0, -1)),
        (1, 3): ((+0, +1), (-2, +1), (-1, +1), (-2, +0), (-1, +0)),
        (2, 0): ((+1, +0), (+1, -1), (+1, +1), (+0, -1), (+0, +1)),
        (3, 1): ((+0, -1), (-2, -1), (-1, -1), (-2, +0), (-1, +0)),
    }

    kicks = SRS.kicks | _override
    i_kicks = SRS.i_kicks | _override


class NoKicks(SRS):
    kicks = {}
    i_kicks = {}
