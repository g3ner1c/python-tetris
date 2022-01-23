import curses
import time

import tetris
from tetris import Move

game = tetris.BaseGame()

moves: dict[int, Move] = {
    ord("z"): Move.rotate(-1),
    curses.KEY_UP: Move.rotate(+1),
    curses.KEY_LEFT: Move.left(),
    curses.KEY_RIGHT: Move.right(),
    curses.KEY_DOWN: Move.soft_drop(),
    ord(" "): Move.hard_drop(),
    ord("c"): Move.swap(),
}


@curses.wrapper
def main(screen: curses.window) -> None:
    curses.use_default_colors()

    for i in range(8):
        curses.init_pair(i, i, -1)

    curses_colors = [
        curses.COLOR_BLACK,
        curses.COLOR_BLUE,
        curses.COLOR_CYAN,
        curses.COLOR_GREEN,
        curses.COLOR_MAGENTA,
        curses.COLOR_RED,
        curses.COLOR_WHITE,
        curses.COLOR_YELLOW,
    ]

    black, blue, cyan, green, magenta, red, white, yellow = (
        curses.color_pair(i) for i in curses_colors
    )

    colors = {
        " ": curses.A_NORMAL,
        "I": cyan,
        "L": yellow,
        "J": blue,
        "S": green,
        "Z": red,
        "T": magenta,
        "O": yellow,
        "X": black,
        "@": white,
    }

    curses.curs_set(0)
    screen.nodelay(True)
    board = screen.subwin(22, 22, 3, 5)
    status = screen.subwin(22, 20, 3, 28)

    def render() -> None:
        screen.clear()
        for y, line in enumerate(game.render().splitlines()):
            for x, ch in enumerate(line):
                paint = colors[ch]
                if not game.playing:
                    paint = paint | curses.A_DIM

                if ch not in [" ", "@", "X"]:
                    ch = "[]"

                board.addstr(y + 1, x * 2 + 1, ch, paint)

        status.addstr(1, 2, " Queue ", curses.A_STANDOUT)
        for i, piece in enumerate(game.queue[:4]):
            status.addstr(2, 4 + i * 3, piece.name + ",", colors[piece.name])

        status.addstr(4, 2, " Hold ", curses.A_STANDOUT)
        if game.hold is not None:
            status.addstr(5, 4, game.hold.name + " piece", colors[game.hold.name])

        else:
            status.addstr(5, 4, ". . .", curses.A_DIM)

        if game.lost:
            board.addstr(11, 2, "    Game over!    ", curses.A_REVERSE | red)

        if game.paused:
            board.addstr(11, 2, "      Paused      ", curses.A_REVERSE | yellow)

        status.addstr(7, 2, " Score ", curses.A_STANDOUT)
        status.addstr(8, 2, format(game.score, ","))

        status.addstr(11, 2, "    Controls    ", curses.A_STANDOUT)
        status.addstr(
            13,
            0,
            (
                "  rotate:   z / up  "
                "  move: l/r arrows  "
                "  soft drop:  down  "
                "  hard drop: space  "
                "  swap piece:    c  "
                "  pause:         p  "
                "  restart:       r  "
                "  quit: Ctrl-C / q  "
            ),
        )

        board.border()
        status.border()

    try:
        while True:
            render()
            game.tick()
            ch = screen.getch()
            if ch == ord("q"):
                break

            elif ch == ord("p"):
                game.pause()

            elif ch == ord("r"):
                game.reset()

            elif ch in moves:
                game.push(moves[ch])

            time.sleep(1 / 120)

    except KeyboardInterrupt:
        pass
