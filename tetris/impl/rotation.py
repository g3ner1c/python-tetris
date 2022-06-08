"""Collection of rotation systems and kick tables."""

from __future__ import annotations

from typing import ClassVar, Optional

from tetris.engine import RotationSystem
from tetris.types import Board
from tetris.types import Minos
from tetris.types import Piece
from tetris.types import PieceType

KickTable = dict[tuple[int, int], tuple[tuple[int, int], ...]]  # pardon

# Note: the x and y axes are switched from the usual convention,
# and the x axis (vertical) is inverted to start from top-to-bottom.
# This is because arrays are indexed from the top-to-bottom, left-to-right.


def convert_coords(
    coords: tuple[int, int], board: Optional[Board] = None
) -> tuple[int, int]:
    """Convert a conventional coordinate to a coordinate used by this library.

    This is a function for converting from conventional to internal coordinates
    meant to help with implementing rotation systems, as well as a general
    utility function.

    Parameters
    ----------
    coords : tuple[int, int]
        The conventional (x, y) coordinate.
    board : tetris.types.Board or None, default = None
        The board this coordinate is relative to.

        Set to `None` to convert kick table coordinates and coordinates
        relative to a piece position.`

    Returns
    -------
    tuple[int, int]
        The converted internal coordinate.

    Notes
    -----
    Indexing starts at 0, so the top-left corner (e.g. `(0, 39)` on a 10x40
    board) is `(0, 0)` when converted.

    Examples
    --------
    >>> tetris.impl.rotation.convert_coords((3, 2), game.board)
    (37, 3)
    >>> tetris.impl.rotation.convert_coords((-1, 2))
    (-2, -1)
    """
    if board is None:
        return (-coords[1], coords[0])
    return (board.shape[0] - coords[1] - 1, coords[0])


class SRS(RotationSystem):
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
            #    . . . .
            #    [][][][]
            #    . . . .
            #    . . . .
            ((0, 2), (1, 2), (2, 2), (3, 2)),
            #    . . [].
            #    . . [].
            #    . . [].
            #    . . [].
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            #    . . . .
            #    . . . .
            #    [][][][]
            #    . . . .
            ((0, 1), (1, 1), (2, 1), (3, 1)),
            #    . []. .
            #    . []. .
            #    . []. .
            #    . []. .
        ],
        PieceType.L: [
            ((0, 2), (1, 0), (1, 1), (1, 2)),
            #    . . []
            #    [][][]
            #    . . .
            ((0, 1), (1, 1), (2, 1), (2, 2)),
            #    . [] .
            #    . [] .
            #    . [][]
            ((1, 0), (1, 1), (1, 2), (2, 0)),
            #    . . .
            #    [][][]
            #    []. .
            ((0, 0), (0, 1), (1, 1), (2, 1)),
            #    [][] .
            #    . [] .
            #    . [] .
        ],
        PieceType.J: [
            ((0, 0), (1, 0), (1, 1), (1, 2)),
            #    []. .
            #    [][][]
            #    . . .
            ((0, 1), (0, 2), (1, 1), (2, 1)),
            #    . [][]
            #    . [] .
            #    . [] .
            ((1, 0), (1, 1), (1, 2), (2, 2)),
            #    . . .
            #    [][][]
            #    . . []
            ((0, 1), (1, 1), (2, 0), (2, 1)),
            #    . [] .
            #    . [] .
            #    [][] .
        ],
        PieceType.S: [
            ((0, 1), (0, 2), (1, 0), (1, 1)),
            #    . [][]
            #    [][].
            #    . . .
            ((0, 1), (1, 1), (1, 2), (2, 2)),
            #    . [] .
            #    . [][]
            #    . . []
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            #    . . .
            #    . [][]
            #    [][].
            ((0, 0), (1, 0), (1, 1), (2, 1)),
            #    []. .
            #    [][].
            #    . [].
        ],
        PieceType.Z: [
            ((0, 0), (0, 1), (1, 1), (1, 2)),
            #    [][].
            #    . [][]
            #    . . .
            ((0, 2), (1, 1), (1, 2), (2, 1)),
            #    . . []
            #    . [][]
            #    . [] .
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            #    . . .
            #    [][].
            #    . [][]
            ((0, 1), (1, 0), (1, 1), (2, 0)),
            #    . [].
            #    [][].
            #    []. .
        ],
        PieceType.T: [
            ((0, 1), (1, 0), (1, 1), (1, 2)),
            #    . [].
            #    [][][]
            #    . . .
            ((0, 1), (1, 1), (1, 2), (2, 1)),
            #    . [].
            #    . [][]
            #    . [].
            ((1, 0), (1, 1), (1, 2), (2, 1)),
            #    . . .
            #    [][][]
            #    . [].
            ((0, 1), (1, 0), (1, 1), (2, 1)),
            #    . [].
            #    [][].
            #    . [].
        ],
        PieceType.O: [
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            # nothing happens lol
            #    . [][].
            #    . [][].
        ],
    }

    # remember that the conventional (x, y) -> (-y, x) because of the axis changes
    # 0: spawn
    # 1: R, 90° clockwise turn from spawn
    # 2: 180° from spawn
    # 3: L, 90° counter-clockwise turn from spawn

    kicks: ClassVar[KickTable] = {
        # (kick_from, kick_to): (offset1, offset2, offset3, offset4)
        (0, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),  # 0 -> R | CW
        (0, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),  # 0 -> L | CCW
        (1, 0): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),  # R -> 0 | CCW
        (1, 2): ((+0, +1), (+1, +1), (-2, +0), (-2, +1)),  # R -> 2 | CW
        (2, 1): ((+0, -1), (-1, -1), (+2, +0), (+2, -1)),  # 2 -> R | CCW
        (2, 3): ((+0, +1), (-1, +1), (+2, +0), (+2, +1)),  # 2 -> L | CW
        (3, 0): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),  # L -> 0 | CW
        (3, 2): ((+0, -1), (+1, -1), (-2, +0), (-2, -1)),  # L -> 2 | CCW
    }

    i_kicks: ClassVar[KickTable] = {
        (0, 1): ((+0, -1), (+0, +1), (+1, -2), (-2, +1)),  # 0 -> R | CW
        (0, 3): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),  # 0 -> L | CCW
        (1, 0): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),  # R -> 0 | CCW
        (1, 2): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),  # R -> 2 | CW
        (2, 1): ((+0, +1), (+0, -2), (+2, +1), (-1, +2)),  # 2 -> R | CCW
        (2, 3): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),  # 2 -> L | CW
        (3, 0): ((+0, +1), (+0, -2), (+2, +1), (-1, -2)),  # L -> 0 | CW
        (3, 2): ((+0, -2), (+0, +1), (+1, -2), (-2, +1)),  # L -> 2 | CCW
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
        minos = self.shapes[piece.type][to_r]  # sets minos to new rotated shape

        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            # if piece doesn't overlap with anything, rotate it
            piece.r = to_r

        elif (piece.r, to_r) in self.kicks:
            # if piece overlaps with something, try to kick it
            if piece.type == PieceType.I:
                table = self.i_kicks

            else:
                table = self.kicks

            kicks = table[piece.r, to_r]

            for x, y in kicks:
                # for each offset, test if it's valid
                if not self.overlaps(minos=minos, px=piece.x + x, py=piece.y + y):
                    # if it's valid, kick it and break
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
