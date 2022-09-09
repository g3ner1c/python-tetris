"""Collection of rotation systems and kick tables."""

from __future__ import annotations

from typing import ClassVar, Optional

from tetris.engine import RotationSystem
from tetris.types import Board, Minos, Piece, PieceType, Rule, Ruleset

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
        (0, 1): ((+0, -2), (+0, +1), (+1, -2), (-2, +1)),  # 0 -> R | CW
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

        # find x position of lowest block
        spawn_x = 0
        for coor in self.shapes[piece][0]:
            # could replace with dict but this is rotation system independent
            if coor[0] > spawn_x:
                spawn_x = coor[0]

        # lowest block spawns at one row above top row of visible area
        spawn_x = (mx // 2 - 1) - spawn_x

        spawn_y = (my + 3) // 2 - 3  # left-aligned centre-ish
        minos = self.shapes[piece][0]

        # if top row isn't blocked move down
        if not self.overlaps(minos=minos, px=spawn_x, py=spawn_y) and not self.overlaps(
            minos=minos, px=spawn_x + 1, py=spawn_y
        ):
            spawn_x += 1

        return Piece(
            type=piece,
            x=spawn_x,
            y=spawn_y,
            r=0,
            minos=minos,
        )

    def rotate(self, piece: Piece, r: int) -> None:  # noqa: D102
        to_r = (piece.r + r) % 4
        minos = self.shapes[piece.type][to_r]  # new piece shape

        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            # if piece doesn't overlap with anything, rotate it
            piece.r = to_r
            piece.minos = minos
            return

        # otherwise, try to kick it
        if piece.type == PieceType.I:
            table = self.i_kicks
        else:
            table = self.kicks

        self.kick_piece(table, piece, to_r)

    def kick_piece(
        self, table: KickTable, piece: Piece, to_r: int
    ) -> None:  # noqa: D102
        if not (piece.r, to_r) in table:
            return

        minos = self.shapes[piece.type][piece.r]
        for x, y in table[piece.r, to_r]:
            # for each offset, test if it's valid
            if not self.overlaps(minos=minos, px=piece.x + x, py=piece.y + y):
                # if it's valid, kick it and break
                piece.x += x
                piece.y += y
                piece.r = to_r
                break

        piece.minos = self.shapes[piece.type][piece.r]


class TetrioSRS(SRS):
    """TETR.IO's custom version of SRS.

    TETR.IO's implementation of SRS also uses its own 180° kick table, which is
    not used in guideline SRS. This rotation system also has a ``Rule`` for
    symmetrical I-piece kicks which is on by default, called *SRS+* in-game.
    """

    tetrio_180_kicks: ClassVar[KickTable] = {
        (0, 2): ((-1, +0), (-1, +1), (-1, -1), (+0, +1), (+0, -1)),  # 0 -> 2
        (1, 3): ((+0, +1), (-2, +1), (-1, +1), (-2, +0), (-1, +0)),  # R -> L
        (2, 0): ((+1, +0), (+1, -1), (+1, +1), (+0, -1), (+0, +1)),  # 2 -> 0
        (3, 1): ((+0, -1), (-2, -1), (-1, -1), (-2, +0), (-1, +0)),  # L -> R
    }

    srs_plus_i_kicks: ClassVar[KickTable] = {  # symmetrical I kicks (SRS+)
        (0, 1): ((+0, +1), (+0, -2), (+1, -2), (-2, +1)),  # 0 -> R | CW
        (0, 3): ((+0, -1), (+0, +2), (+1, +2), (-2, -1)),  # 0 -> L | CCW
        (1, 0): ((+0, -1), (+0, +2), (+2, -1), (-1, +2)),  # R -> 0 | CCW
        (1, 2): ((+0, -1), (+0, +2), (-2, -1), (+1, +2)),  # R -> 2 | CW
        (2, 1): ((+0, -2), (+0, +1), (-1, -2), (+2, +1)),  # 2 -> R | CCW
        (2, 3): ((+0, +2), (+0, -1), (-1, +2), (+2, -1)),  # 2 -> L | CW
        (3, 0): ((+0, +1), (+0, -2), (+2, +1), (-1, -2)),  # L -> 0 | CW
        (3, 2): ((+0, +1), (+0, -2), (-2, +1), (+1, -2)),  # L -> 2 | CCW
    }
    srs_plus_i_kicks |= tetrio_180_kicks

    kicks = SRS.kicks | tetrio_180_kicks
    i_kicks = SRS.i_kicks | tetrio_180_kicks

    def __init__(self, board: Board):
        super().__init__(board)

        self.rules = Ruleset(Rule("srs_plus", bool, True), name="tetrio_srs")

    def rotate(self, piece: Piece, r: int) -> None:  # noqa: D102
        to_r = (piece.r + r) % 4
        minos = self.shapes[piece.type][to_r]
        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            piece.r = to_r
            piece.minos = minos
            return

        if piece.type == PieceType.I:
            if self.rules.srs_plus:
                table = self.srs_plus_i_kicks
            else:
                table = self.i_kicks
        else:
            table = self.kicks

        self.kick_piece(table, piece, to_r)


class NRS(RotationSystem):
    """The NRS rotation system.

    NRS, aka Nintendo Rotation System, is the rotation system used in the
    Nintendo NES and Game Boy Tetris games. This rotation system does not have
    kicks. The right-handed variant of NRS is used in NES Tetris, while
    the left-handed variant is used in Game Boy Tetris.

    Notes
    -----
    This class by default uses the NES right-handed variant because it is more
    popular and well known.
    """

    shapes: dict[PieceType, list[Minos]] = {
        PieceType.I: [
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            #    . . . .
            #    . . . .
            #    [][][][]
            #    . . . .
            ((0, 2), (1, 2), (2, 2), (3, 2)),
            #    . . [].
            #    . . [].
            #    . . [].
            #    . . [].
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            #    repeats
            ((0, 2), (1, 2), (2, 2), (3, 2)),
        ],
        PieceType.L: [
            ((1, 0), (1, 1), (1, 2), (2, 0)),
            #    . . .
            #    [][][]
            #    []. .
            ((0, 0), (0, 1), (1, 1), (2, 1)),
            #    [][] .
            #    . [] .
            #    . [] .
            ((0, 2), (1, 0), (1, 1), (1, 2)),
            #    . . []
            #    [][][]
            #    . . .
            ((0, 1), (1, 1), (2, 1), (2, 2)),
            #    . [] .
            #    . [] .
            #    . [][]
        ],
        PieceType.J: [
            ((1, 0), (1, 1), (1, 2), (2, 2)),
            #    . . .
            #    [][][]
            #    . . []
            ((0, 1), (1, 1), (2, 0), (2, 1)),
            #    . [] .
            #    . [] .
            #    [][] .
            ((0, 0), (1, 0), (1, 1), (1, 2)),
            #    []. .
            #    [][][]
            #    . . .
            ((0, 1), (0, 2), (1, 1), (2, 1)),
            #    . [][]
            #    . [] .
            #    . [] .
        ],
        PieceType.S: [
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            #    . . .
            #    . [][]
            #    [][].
            ((0, 1), (1, 1), (1, 2), (2, 2)),
            #    . [] .
            #    . [][]
            #    . . []
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            #    repeats
            ((0, 1), (1, 1), (1, 2), (2, 2)),
        ],
        PieceType.Z: [
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            #    . . .
            #    [][].
            #    . [][]
            ((0, 2), (1, 1), (1, 2), (2, 1)),
            #    . . []
            #    . [][]
            #    . [] .
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            #    repeats
            ((0, 2), (1, 1), (1, 2), (2, 1)),
        ],
        PieceType.T: [
            ((1, 0), (1, 1), (1, 2), (2, 1)),
            #    . . .
            #    [][][]
            #    . [].
            ((0, 1), (1, 0), (1, 1), (2, 1)),
            #    . [].
            #    [][].
            #    . [].
            ((0, 1), (1, 0), (1, 1), (1, 2)),
            #    . [].
            #    [][][]
            #    . . .
            ((0, 1), (1, 1), (1, 2), (2, 1)),
            #    . [].
            #    . [][]
            #    . [].
        ],
        PieceType.O: [
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2)),
            #    [][]
            #    [][]
        ],
    }

    gb_shapes = shapes | {
        PieceType.I: [
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
            ((2, 0), (2, 1), (2, 2), (2, 3)),
            #    repeats
            ((0, 1), (1, 1), (2, 1), (3, 1)),
        ],
        PieceType.S: [
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            #    . . .
            #    . [][]
            #    [][].
            ((0, 0), (1, 0), (1, 1), (2, 1)),
            #    []. .
            #    [][].
            #    . [].
            ((1, 1), (1, 2), (2, 0), (2, 1)),
            #    repeats
            ((0, 0), (1, 0), (1, 1), (2, 1)),
        ],
        PieceType.Z: [
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            #    . . .
            #    [][].
            #    . [][]
            ((0, 1), (1, 0), (1, 1), (2, 0)),
            #    . [].
            #    [][].
            #    []. .
            ((1, 0), (1, 1), (2, 1), (2, 2)),
            #    repeats
            ((0, 1), (1, 0), (1, 1), (2, 0)),
        ],
    }

    def __init__(self, board: Board):
        super().__init__(board)

        self.rules = Ruleset(Rule("game_boy", bool, False), name="nrs")

    def spawn(self, piece: PieceType) -> Piece:  # noqa: D102
        if self.rules.game_boy:
            shapes = self.gb_shapes
        else:
            shapes = self.shapes

        mx, my = self.board.shape

        # find x position of highest block
        spawn_x = 3
        for x, _ in shapes[piece][0]:
            if x < spawn_x:
                spawn_x = x

        # highest block spawns at top row of visible area
        spawn_x = (mx // 2) - spawn_x

        if self.rules.game_boy:
            # game boy spawns at 3 rows below top (row 17 for 10x20 playfield)
            spawn_x += 3

        return Piece(
            type=piece,
            x=spawn_x,
            y=(my + 3) // 2 - 3,
            r=0,
            minos=shapes[piece][0],
        )

    def rotate(self, piece: Piece, r: int) -> None:  # noqa: D102
        if self.rules.game_boy:
            shapes = self.gb_shapes
        else:
            shapes = self.shapes

        to_r = (piece.r + r) % 4
        minos = shapes[piece.type][to_r]
        if not self.overlaps(minos=minos, px=piece.x, py=piece.y):
            piece.r = to_r
            piece.minos = minos
