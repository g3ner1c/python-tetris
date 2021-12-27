import curses

import tetris

game = tetris.BaseGame()

keymap: dict[str, int] = {
    "rotate-left": ord("z"),
    "rotate-right": curses.KEY_UP,
    "move-left": curses.KEY_LEFT,
    "move-right": curses.KEY_RIGHT,
    "soft-drop": curses.KEY_DOWN,
    "hard-drop": ord(" "),
    "swap": ord("c"),
    "quit": ord("q"),
}


@curses.wrapper
def main(screen: curses.window) -> None:
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_CYAN, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    colors = {
        " ": curses.A_NORMAL,
        "I": curses.color_pair(6),
        "L": curses.color_pair(3),
        "J": curses.color_pair(4),
        "S": curses.color_pair(2),
        "Z": curses.color_pair(1),
        "T": curses.color_pair(5),
        "O": curses.color_pair(3),
        "X": curses.A_DIM,
        "@": curses.color_pair(7),
    }

    curses.curs_set(0)
    board = screen.subwin(22, 22, 3, 5)
    status = screen.subwin(22, 20, 3, 28)

    def render() -> None:
        screen.clear()
        for y, line in enumerate(game.render().splitlines()):
            for x, ch in enumerate(line):
                paint = colors[ch]
                if ch not in [" ", "@"]:
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

        status.addstr(7, 2, " Score ", curses.A_STANDOUT)
        status.addstr(8, 2, format(game.score, ","))

        status.addstr(14, 2, "    Controls    ", curses.A_STANDOUT)
        status.addstr(
            16,
            0,
            (
                "  rotate:   z / up  "
                "  move: l/r arrows  "
                "  soft drop:  down  "
                "  hard drop: space  "
                "  swap piece:    c  "
            ),
        )

        board.border()
        status.border()

    try:
        while True:
            render()
            ch = screen.getch()

            if ch == keymap["quit"]:
                break
            if ch == keymap["rotate-left"]:
                game.rotate(turns=-1)
            if ch == keymap["rotate-right"]:
                game.rotate(turns=+1)
            if ch == keymap["move-left"]:
                game.drag(y=-1)
            if ch == keymap["move-right"]:
                game.drag(y=+1)
            if ch == keymap["soft-drop"]:
                game.soft_drop()
            if ch == keymap["hard-drop"]:
                game.hard_drop()
            if ch == keymap["swap"]:
                game.swap()

    except KeyboardInterrupt:
        pass
