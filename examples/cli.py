import curses
import time

import tetris
from tetris import MinoType
from tetris import Move


@curses.wrapper
def main(screen: curses.window) -> None:
    game_start = time.monotonic()
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
        MinoType.EMPTY: curses.A_NORMAL,
        MinoType.I: cyan,
        MinoType.L: yellow,
        MinoType.J: blue,
        MinoType.S: green,
        MinoType.Z: red,
        MinoType.T: magenta,
        MinoType.O: yellow,
        MinoType.GARBAGE: black,
        MinoType.GHOST: white,
    }

    curses.curs_set(0)
    screen.nodelay(True)

    def render() -> None:
        screen.erase()
        my, mx = screen.getmaxyx()
        board = screen.subwin(22, 22, my // 2 - 11, mx // 2 - 22)
        status = screen.subwin(22, 20, my // 2 - 11, 23 + mx // 2 - 22)
        for x, line in enumerate(game.playfield):
            for y, i in enumerate(line):
                paint = colors[i]
                ch = "[]"
                if i == MinoType.GARBAGE:
                    ch = "X "
                elif i == MinoType.GHOST:
                    ch = "@ "
                elif i == MinoType.EMPTY:
                    ch = "  "

                board.addstr(x + 1, y * 2 + 1, ch, paint)

        status.addstr(1, 2, " Queue ", curses.A_STANDOUT)
        for i, piece in enumerate(game.queue[:4]):
            status.addstr(2, 4 + i * 3, piece.name, colors[piece])  # type: ignore
            if i < 3:
                status.addstr(2, 5 + i * 3, ",", curses.A_DIM)

        status.addstr(4, 2, " Hold ", curses.A_STANDOUT)
        if game.hold is not None:
            status.addstr(
                5, 4, game.hold.name + " piece", colors[game.hold]  # type: ignore
            )

        else:
            status.addstr(5, 4, ". . .", curses.A_DIM)

        status.addstr(7, 2, " Score ", curses.A_STANDOUT)
        status.addstr(8, 4, format(game.score, ","))

        line_clears = game.scorer.line_clears  # type: ignore
        status.addstr(10, 2, " Level ", curses.A_STANDOUT)
        status.addstr(11, 4, f"{game.level}")
        status.addstr(
            11,
            5 + len(str(game.level)),
            f"[{line_clears}/{(line_clears // 10 + 1) * 10}]",
            curses.A_DIM,
        )

        elapsed = time.monotonic() - game_start
        status.addstr(14, 2, " Elapsed ", curses.A_STANDOUT)
        status.addstr(15, 4, f"{int(elapsed / 60)}:{elapsed % 60:0>6.3f}")

        status.addstr(20, 2, "[h]elp for info", curses.A_DIM)

        if game.lost:
            board.addstr(11, 2, "    Game over!    ", curses.A_REVERSE | red)

        if game.paused:
            board.addstr(11, 2, "      Paused      ", curses.A_REVERSE | yellow)

        board.border()
        status.border()

    def render_help() -> None:
        my, mx = screen.getmaxyx()
        help_menu = screen.subwin(16, 33, my // 2 - 8, mx // 2 - 17)
        help_menu.erase()
        help_menu.addstr(2, 5, "♥ dzshn/python-tetris")
        help_menu.addstr(4, 4, " Controls ", curses.A_STANDOUT)
        for i, line in enumerate(
            [
                "rotate          z / ↑",
                "move            ← / →",
                "soft drop           ↓",
                "hard drop           ␣",
                "swap piece          c",
                "pause               p",
                "restart             r",
                "quit       Ctrl-C / q",
            ]
        ):
            help_menu.addstr(i + 6, 6, line)

        help_menu.border()

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
                game_start = time.monotonic()

            elif ch == ord("h"):
                paused = game.paused
                game.pause(state=True)
                screen.nodelay(False)
                render_help()
                screen.getch()
                screen.nodelay(True)
                game.pause(state=paused)

            elif ch in moves:
                game.push(moves[ch])

            time.sleep(1 / 120)

    except KeyboardInterrupt:
        pass
