"""Reference interactive game implementation with curses."""

from __future__ import annotations

import asyncio
import curses
import curses.ascii
import gc
import getopt
import io
import math
import os
import platform
import shutil
import signal
import statistics
import sys
import time
from configparser import ConfigParser
from contextlib import suppress
from pathlib import Path
from typing import Any, Literal, Optional, Union

import tetris
from tetris import MinoType

if sys.version_info > (3, 10):
    from typing import TypeAlias

    Layout: TypeAlias

Layout = list[
    Union[
        tuple[str, Literal["normal", "off"]],
        tuple[str, Literal["choice"], list[str]],
    ]
]

# NOTE: `tracemalloc` may be enabled at runtime, but will not track memory that
# is already allocated. it should be enabled as early as possible by setting
# `PYTHONTRACEMALLOC` to 1 or higher, or providing `-Xtracemalloc`::
#    $ PYTHONTRACEMALLOC=1 tetris
#    $ python -Xtracemalloc tetris
try:
    import tracemalloc
except ImportError:
    USE_TRACEMALLOC = False
else:
    USE_TRACEMALLOC = tracemalloc.is_tracing()

PYPY = sys.implementation.name == "pypy"
CPYTHON = sys.implementation.name == "cpython"

flag_names = []
for flag in sys.abiflags:
    if flag == "d":
        flag_names.append("debug")
    elif flag == "m":
        flag_names.append("pymalloc")
    elif flag == "u":
        flag_names.append("wide-uc")
if flag_names:
    FLAGS = sys.abiflags + " [" + "+".join(flag_names) + "]"
else:
    FLAGS = sys.abiflags
VERSION = f"python-tetris {tetris.__version__}"
# e.g. `CPython 3.10.0d [debug] on Linux`
ENVIRONMENT = "%s %s%s on %s" % (
    platform.python_implementation(),
    platform.python_version(),
    FLAGS,
    platform.system(),
)
FQDN = "xyz.dzshn.tetris"
USAGE = f"""\
tetris {tetris.__version__}
Sofia <me@dzshn.xyz>

Usage:
    tetris [flags]

Flags:
    -h, --help         This message!
    -p, --path <PATH>  Specify directory to store data [default: os-dependent]
    --clear            Clear all user data and exit
    --version          Output the version and exit\
"""
DEFAULTS: dict[str, dict[str, Any]] = {
    "render": {
        "framerate": 80,
    },
    "debug": {"always_on": False},
    "keymap": {
        "pause": f"{ord('p')},{curses.ascii.ESC}",
        "harddrop": ord("w"),
        "left": ord("a"),
        "softdrop": ord("s"),
        "right": ord("d"),
        "rleft": ord("j"),
        "rright": ord("k"),
        "r180": ord("l"),
        "swap": ord("q"),
        "debug": curses.KEY_F3,
    },
}
MOVES = {
    "harddrop": tetris.Move.hard_drop(),
    "left": tetris.Move.left(),
    "softdrop": tetris.Move.soft_drop(),
    "right": tetris.Move.right(),
    "rleft": tetris.Move.rotate(-1),
    "rright": tetris.Move.rotate(+1),
    "r180": tetris.Move.rotate(2),
    "swap": tetris.Move.swap(),
}
PRESETS = {
    "modern": tetris.impl.presets.Modern,
    "nestris": tetris.impl.presets.NES,
}
# foregound and background colors, 4-bit and 8-bit versions
COLORS = {
    "default": ((255, 15), (233, 0)),
    "reverse": ((232, 0), (255, 15)),
    "selection": ((255, 0), (235, 15)),
    MinoType.EMPTY.value: (None, None),
    MinoType.GARBAGE.value: (None, None),
    MinoType.GHOST.value: (None, None),
    MinoType.I.value: ((87, 14), None),
    MinoType.L.value: ((214, 11), None),
    MinoType.J.value: ((81, 12), None),
    MinoType.S.value: ((77, 10), None),
    MinoType.Z.value: ((196, 9), None),
    MinoType.T.value: ((92, 13), None),
    MinoType.O.value: ((220, 11), None),
}
PALETTE = {
    # basic 4-bit colors
    0: 0x151515,
    9: 0xEB4763,
    10: 0x2EDC76,
    11: 0xFDC835,
    12: 0x00B8F5,
    13: 0xA873E8,
    14: 0x13C5F6,
    15: 0xF0F0F0,
    # 8-bit colors
    87: 0x13C5F6,
    214: 0xF18F01,
    81: 0x00B8F5,
    77: 0x2EDC76,
    196: 0xEB4763,
    92: 0xA873E8,
    220: 0xFDC835,
    233: 0x151515,
    255: 0xF0F0F0,
}
EMPTY = MinoType.EMPTY.value
GHOST = MinoType.GHOST.value


def guess_data_path() -> Optional[Path]:
    """Find a suitable path for user data.

    Returns
    -------
    pathlib.Path or None
    """
    paths = []

    if platform.system() == "Darwin":
        paths.append(Path("~/Library/Application Support") / FQDN)

    if p := os.getenv("XDG_DATA_HOME"):
        paths.append(Path(p) / FQDN)

    if platform.system() == "Windows":
        paths.append(Path(os.getenv("APPDATA") or "~") / FQDN)

    paths.append(Path("~/.local/share") / FQDN)
    paths.append(Path("~/." + FQDN))

    for path in paths:
        path = path.expanduser()
        if path.parent.exists():
            return path

    return None


def get_memory_info() -> list[str]:
    """Return memory info according to the interpreter, if possible."""
    if PYPY:
        stats: Any = gc.get_stats()
        return [
            f"Mem: {stats.memory_used_sum} (↑{stats.peak_memory})",
            f"Allocated: {stats.memory_allocated_sum}",
        ]
    if CPYTHON:
        if USE_TRACEMALLOC:
            mem, peak = tracemalloc.get_traced_memory()
            return [
                f"Mem: {mem // 1000}kB (↑{peak // 1000}kB)",
                f"Allocated: {sys.getallocatedblocks()}",
                "GC: %i %i %i" % gc.get_count(),
            ]
        return ["Mem: [tracemalloc disabled]"]
    # XXX: psutil fallback maybe?
    return []


class TetrisTUI:
    """TUI Tetris game."""

    def __init__(self, config: Optional[str] = None):
        self.cfg = ConfigParser()
        self.cfg.read_dict(DEFAULTS)

        if config is None:
            self.path = guess_data_path()
        elif config == os.devnull:
            self.path = None
        else:
            self.path = Path(config)
        if self.path is not None:
            self.path.mkdir(exist_ok=True)
            try:
                with open(self.path / "tetris.conf", "x") as f:
                    self.cfg.write(f)
            except FileExistsError:
                with open(self.path / "tetris.conf") as f:
                    self.cfg.read_string(f.read())

        self.keymap = {
            action: {int(k) for k in keys.split(",")}
            for action, keys in self.cfg["keymap"].items()
        }
        # update rate and it's reciprocal
        self.hz = self.cfg["render"].getint("framerate")
        self.rhz = 1 / self.hz
        # frame delays, cleared every second
        self.frames: list[float] = []
        # current average
        self.fps = 0.0
        # last tick delay
        self.tick = 0.0
        # debug menu toggle
        self.debug = self.cfg["debug"].getboolean("always_on")
        self.scene: Scene = MainMenu(self)
        # combined stdout/stderr replacement
        self.output = io.StringIO()

    async def main(self) -> None:
        """Application loop."""
        sys.stdout = sys.stderr = self.output
        self.screen = curses.initscr()
        curses.savetty()
        try:
            await self.setup()
            while True:
                await self.render()
                ch = self.screen.getch()
                if ch == -1:
                    continue
                if ch == ord("c") & 0x1F:  # Ctrl+C
                    raise KeyboardInterrupt
                if ch == ord("z") & 0x1F:  # Ctrl+Z
                    if not hasattr(os, "kill") and hasattr(signal, "SIGTSTP"):
                        # SIGTSTP is *nix-only
                        continue
                    if isinstance(self.scene, GameScene):
                        self.scene.game.pause(True)
                    os.kill(os.getpid(), signal.SIGTSTP)
                if ch == curses.KEY_RESIZE:
                    await self.on_resize()
                elif ch in self.keymap["debug"]:
                    self.debug = not self.debug
                else:
                    await self.scene.on_ch(ch)
        finally:
            curses.resetty()
            curses.endwin()

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print(self.output.getvalue(), end="")

    async def setup(self) -> None:
        """Prepare the TUI for the main loop."""
        curses.noecho()
        curses.raw(True)
        self.screen.keypad(True)
        self.screen.nodelay(True)
        with suppress(AttributeError, curses.error):
            curses.set_escdelay(4)
        with suppress(curses.error):
            curses.curs_set(0)
        with suppress(curses.error):
            curses.start_color()

        color_count = getattr(curses, "COLORS", 0)
        for i, color in PALETTE.items():
            if i <= 16 and color_count < 16:  # VGA graphics :3
                i %= 8
            if i >= color_count:
                continue
            r, g, b = color.to_bytes(3, "big")
            with suppress(curses.error):
                curses.init_color(
                    i,
                    int((r / 256) * 1000),
                    int((g / 256) * 1000),
                    int((b / 256) * 1000),
                )
        self.colors = {}
        default_fg, default_bg = COLORS["default"]
        assert default_fg is not None and default_bg is not None
        for i, (name, colors) in enumerate(COLORS.items()):
            fg = colors[0] or default_fg
            bg = colors[1] or default_bg
            if color_count >= 256:
                # 8-bit color, use default
                curses.init_pair(i + 1, fg[0], bg[0])
                self.colors[name] = curses.color_pair(i + 1)
            elif color_count >= 16:
                # 4-bit color, use fallback
                curses.init_pair(i + 1, fg[1], bg[1])
                self.colors[name] = curses.color_pair(i + 1)
            elif color_count >= 8:
                # 3-bit color, use fallback mod 8 (only bright colors)
                curses.init_pair(i + 1, fg[1] % 8, bg[1] % 8)
                self.colors[name] = curses.color_pair(i + 1)
            else:
                # no color support
                self.colors[name] = 0

        self.screen.bkgd(" ", self.colors["default"])

        await self.on_resize()

        self.debug_lines: list[str] = []
        self.debug_renderer = asyncio.create_task(self.render_debug())

    async def on_resize(self) -> None:
        """Update UI dependant on terminal size."""
        self.my, self.mx = self.screen.getmaxyx()
        self.screen.clear()
        await self.scene.on_resize()

    async def render(self) -> None:
        """Render the screen."""
        t = time.perf_counter()

        await self.scene.render()

        if self.debug:
            if self.debug_renderer.done():
                exc = self.debug_renderer.exception()
                raise RuntimeError("debug renderer task died!") from exc
            for i, ln in enumerate(self.debug_lines):
                self.screen.addstr(i, 0, ln, self.colors["reverse"])

            for i, ln in enumerate(self.output.getvalue().splitlines()[:-16:-1]):
                self.screen.addstr(self.my - i - 1, 0, ln, self.colors["reverse"])

        # Recalculate average every 1 second
        if len(self.frames) >= self.hz:
            self.fps = 1 / statistics.fmean(self.frames)
            self.frames.clear()

        # Sleep until next multiple of framerate
        await asyncio.sleep(self.rhz - time.perf_counter() % self.rhz)

        self.frames.append(time.perf_counter() - t)

    async def render_debug(self) -> None:
        """Render the debug menu, if active."""
        color_count = getattr(curses, "COLORS", 0)
        if color_count == 0:
            terminal = "1-bit"
        elif (bits := math.log2(color_count)) % 1 == 0:
            terminal = f"{bits:.0f}-bit"
        else:
            terminal = f"{color_count} colors"
        terminal += f" ({os.getenv('TERM')})"
        if curses.can_change_color():
            terminal += " +palette"
        while True:
            if self.debug:
                lines = []
                lines.append(VERSION)
                lines.append(ENVIRONMENT)
                lines.append(f"{self.fps:.0f} fps")
                lines.append(f"@ {self.tick*1e6:.0f}us ticks")
                lines.extend(get_memory_info())
                lines.append(f"Display: {self.my}x{self.mx} {terminal}")
                lines.append(type(self.scene).__name__)
                lines.extend(await self.scene.render_debug())
                self.debug_lines = lines

            await asyncio.sleep((1 / 20) - time.perf_counter() % (1 / 20))

    async def switch_scene(
        self, new_scene: type[Scene], *args: Any, **kwargs: Any
    ) -> None:
        """Switch to a new scene."""
        self.scene = new_scene(self, *args, **kwargs)
        await self.scene.on_resize()

    def centeredsubwin(
        self, sy: int, sx: int, dy: int = 0, dx: int = 0
    ) -> curses.window:
        """Return a subwindow centered relative to the screen."""
        return self.screen.subwin(
            sy, sx, (self.my - sy + dy) // 2, (self.mx - sx + dx) // 2
        )


class Scene:
    """Object used in dynamic rendering of independent windows."""

    def __init__(self, tui: TetrisTUI):
        self.tui = tui

    @property
    def screen(self) -> curses.window:
        """Shorthand for `tui.screen`."""
        return self.tui.screen

    @property
    def colors(self) -> dict[Any, int]:
        """Shorthand for `tui.colors`."""
        return self.tui.colors

    async def on_resize(self) -> None:
        """Resize event."""
        ...

    async def render(self) -> None:
        """Render the scene."""
        ...

    async def render_debug(self) -> list[str]:
        """Extra debug lines for the scene."""
        return []

    async def on_ch(self, ch: int) -> None:
        """Input event."""
        ...


class Menu(Scene):
    """Scene subclass for menus with a simple layout system."""

    header: Optional[str]
    title: Optional[str]
    cols: int

    def __init__(self, tui: TetrisTUI):
        super().__init__(tui)
        self.selection = 0
        self.values: dict[str, Any] = {}

    @property
    def layout(self) -> Layout:
        """The menu's layout."""
        return self._layout

    @layout.setter
    def layout(self, value: Layout) -> None:
        self._layout = value
        for name, kind, *_ in value:
            if kind == "choice":
                self.values[name] = 0

    async def on_resize(self) -> None:  # noqa: D102
        self.rows = len(self.layout) + 3
        if self.header is not None:
            self.rows += 3
        self.view = self.tui.centeredsubwin(self.rows, self.cols)

    async def render(self) -> None:  # noqa: D102
        self.screen.erase()

        self.view.border()
        if self.title is not None:
            self.view.addstr(0, 2, "[%s]" % self.title)

        if self.header is not None:
            self.view.addstr(2, 3, self.header)
            i = 4
        else:
            i = 1

        for j, (name, kind, *opts) in enumerate(self.layout):
            self.view.addstr(i + j, 3, name)
            if kind == "choice":
                choices = opts[0]
                index = self.values[name]
                fmt = f"  {choices[index]}  "
                if index > 0:
                    fmt = "<" + fmt[1:]
                if index < len(choices) - 1:
                    fmt = fmt[:-1] + ">"
                self.view.addstr(i + j, self.cols - len(fmt) - 2, fmt)

            if self.selection == j:
                self.view.chgat(i + j, 2, 32 - 4, self.colors["selection"])

    async def on_ch(self, ch: int) -> None:  # noqa: D102
        if ch == curses.KEY_UP:
            # move cursor down to the nearest selectable element
            for _ in range(len(self.layout)):
                self.selection -= 1
                self.selection %= len(self.layout)
                if self.layout[self.selection][1] != "off":
                    break
        elif ch == curses.KEY_DOWN:
            # move cursor up to the nearest selectable element
            for _ in range(len(self.layout)):
                self.selection += 1
                self.selection %= len(self.layout)
                if self.layout[self.selection][1] != "off":
                    break
        elif ch == curses.KEY_LEFT:
            name, kind, *opts = self.layout[self.selection]
            if kind == "choice":
                # cycle backwards through options
                choices = opts[0]
                self.values[name] -= 1
                self.values[name] %= len(choices)
        elif ch == curses.KEY_RIGHT:
            name, kind, *opts = self.layout[self.selection]
            if kind == "choice":
                # cycle forwards through options
                choices = opts[0]
                self.values[name] += 1
                self.values[name] %= len(choices)
        elif ch in (curses.KEY_ENTER, ord("\n")):
            # dispatch entry event
            name, kind, *opts = self.layout[self.selection]
            if kind == "choice":
                await self.on_entry(name, opts[0][self.values.get(name, 0)])
            else:
                await self.on_entry(name, None)

    async def on_entry(self, entry: str, value: Any) -> None:
        """Submenu entry event."""
        ...


class MainMenu(Menu):
    """Initial game menu."""

    def __init__(self, tui: TetrisTUI):
        super().__init__(tui)
        self.header = "♥ python-tetris"
        self.title = tetris.__version__
        self.layout = [
            ("quick play", "choice", list(PRESETS)),
            ("new game", "off"),
            ("settings", "off"),
            ("credits", "normal"),
        ]
        self.cols = 32

    async def on_entry(self, entry: str, value: Any) -> Any:  # noqa: D102
        if entry == "quick play":
            await self.tui.switch_scene(GameScene, PRESETS[value], {})
        elif entry == "credits":
            await self.tui.switch_scene(CreditsScene)


class CreditsScene(Scene):
    """Credits sub-menu."""

    async def on_resize(self) -> None:  # noqa: D102
        text = """\
            python-tetris is free software!
            (ﾉ◕ヮ◕)ﾉ*:・ﾟ✧

            Many thanks to Sky (@g3ner1c)

            -*- Support the author -*-
            @  https://patreon.com/dzshn

            -*- Project stuffz -*-
            @ https://github.com/dzshn/python-tetris

            (c) 2021-2022 Sofia N. Lima. MIT License\
        """
        self.screen.erase()
        v = self.tui.centeredsubwin(16, 48)
        v.border()
        for i, ln in enumerate(text.splitlines()):
            ln = ln.strip()
            v.addstr(i + 2, 24 - len(ln) // 2, ln)

    async def on_ch(self, ch: int) -> None:  # noqa: D102
        await self.tui.switch_scene(MainMenu)


class GameScene(Scene):
    """Generic game window."""

    def __init__(
        self,
        tui: TetrisTUI,
        preset: tetris.engine.EngineFactory,
        rules: dict[str, Any],
    ):
        super().__init__(tui)
        self.game = tetris.BaseGame(preset, rules)
        self.action_text: set[str] = set()
        self.previews = {}
        for piece in tetris.PieceType:
            minos = self.game.rs.spawn(piece).minos
            cols = [y for _, y in minos]
            max_col = max(cols)
            min_col = min(cols)
            rows = [x for x, _ in minos]
            max_row = max(rows)
            min_row = min(rows)

            shape = tetris.board.Board.zeros((4, 4))
            for x, y in minos:
                # justify shape so it's bottom is at the second row
                shape[x - min(max_row - 1, min_row), y] = True

            # center the piece within 8 columns
            pad = " " * (4 - max_col + min_col)
            trim = min_col * 2
            self.previews[piece] = [
                pad + "".join("[]" if x else "  " for x in ln)[trim:].rstrip()
                for ln in shape
            ]

    async def on_resize(self) -> None:  # noqa: D102
        self.view = self.tui.centeredsubwin(25, 22, dy=-4)
        self.hold = self.tui.centeredsubwin(4, 10, dy=-18, dx=-30)
        self.queue = self.tui.centeredsubwin(13, 10, dy=-9, dx=30)
        self.stats = self.tui.centeredsubwin(2, 22, dy=23)
        self.left_text = self.tui.centeredsubwin(8, 14, dy=12, dx=-35)

    async def render(self) -> None:  # noqa: D102
        t = time.perf_counter()
        self.game.tick()
        self.tui.tick = time.perf_counter() - t
        self.screen.erase()
        self.view.border()
        for i in range(4):
            self.view.addstr(i, 0, " " * 22)

        for i, ln in enumerate(self.game.get_playfield(buffer_lines=4)):
            for j, x in enumerate(ln):
                if x == EMPTY:
                    ch = "  "
                elif x == GHOST:
                    ch = "@ "
                else:
                    ch = "[]"
                self.view.addstr(i, j * 2 + 1, ch, self.colors[x])

        if self.game.hold:
            for i, ln in enumerate(self.previews[self.game.hold]):
                if ln.strip():
                    self.hold.addstr(i + 1, 0, ln, self.colors[self.game.hold])
        self.hold.border(0, 0, 0, 0, 0, 0, 0, curses.ACS_SBSS)

        for i, piece in enumerate(self.game.queue):
            for j, ln in enumerate(self.previews[piece]):
                if ln.strip():
                    self.queue.addstr(i * 3 + j + 1, 0, ln, self.colors[piece])
        self.queue.border(0, 0, 0, 0, 0, 0, curses.ACS_SSSB, 0)

        scorer = self.game.scorer
        level = f"{scorer.level} [{scorer.line_clears}/{scorer.goal}]"

        self.stats.insstr(0, 0, level.center(22))
        self.stats.insstr(1, 0, format(self.game.score, ",").center(22))

        self.stats.chgat(
            0, 0, int(scorer.line_clears / scorer.goal * 22), self.colors["reverse"]
        )

        left_lines = []
        if (b2b := getattr(self.game.scorer, "back_to_back")) > 1:
            left_lines.append("Back-to-back!")
            left_lines.append(f"[{b2b}x]")
        if (combo := getattr(self.game.scorer, "combo", 0)) > 1:
            left_lines.append(f"{combo}x combo!")

        left_lines.extend(self.action_text)

        for i, line in enumerate(left_lines):
            self.left_text.addstr(i, 14 - len(line), line)

    async def render_debug(self) -> list[str]:  # noqa: D102
        game = self.game
        lines = []
        lines.append("")
        lines.append(f"XYR: {game.piece.x} / {game.piece.y} / {game.piece.r}")
        lines.append("Engine:")
        for part in (game.gravity, game.queue, game.rs, game.scorer):
            lines.append("  " + type(part).__name__)

        return lines

    async def on_ch(self, ch: int) -> None:  # noqa: D102
        if ch in self.tui.keymap["pause"]:
            self.game.pause()
        else:
            for action, keys in self.tui.keymap.items():
                if ch in keys and (move := MOVES.get(action)):
                    self.game.push(move)
                    if getattr(self.game.scorer, "tspin", False):
                        self.action_text.add("T-Spin!")
                    elif "T-Spin!" in self.action_text:
                        self.action_text.remove("T-Spin!")
                    if getattr(self.game.scorer, "tspin_mini", False):
                        self.action_text.add("T-Spin mini!")
                    elif "T-Spin mini!" in self.action_text:
                        self.action_text.remove("T-Spin mini!")
                    break


def main() -> None:
    """Entry point."""
    try:
        opts, _ = getopt.getopt(
            sys.argv[1:], "hp:", ["help", "version", "path=", "clear"]
        )

    except getopt.GetoptError as e:
        print(USAGE)
        print()
        sys.exit(str(e))

    try:
        data_path = None
        for o, v in opts:
            if o in ("-h", "--help"):
                print(USAGE)
                sys.exit(0)
            if o in ("--version",):
                print(VERSION, "@", ENVIRONMENT)
                sys.exit(0)
            if o in ("--clear",):
                path = guess_data_path()
                if path is None or not path.exists():
                    sys.exit(f"nothing to clear (path is {path})")

                if input(f"Clear all data in {path}? [y/N] ") in ("y", "yes"):
                    shutil.rmtree(path)
                    sys.exit(0)

                sys.exit("aborted")
            if o in ("-p", "--path"):
                data_path = v

        asyncio.run(TetrisTUI(data_path).main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
