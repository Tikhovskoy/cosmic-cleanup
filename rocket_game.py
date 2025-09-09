import asyncio
import curses
import random
import time
import itertools

from curses_helpers import draw_frame, get_frame_size, read_controls

TIC_TIMEOUT = 0.1
STAR_SYMBOLS = "+*.:"


async def blink(canvas, row, col, symbol="*", offset_ticks=1):
    while True:
        canvas.addstr(row, col, symbol, curses.A_DIM)
        for _ in range(offset_ticks):
            await asyncio.sleep(0)
        canvas.addstr(row, col, symbol)
        for _ in range(3):
            await asyncio.sleep(0)
        canvas.addstr(row, col, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)
        canvas.addstr(row, col, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def split_frames(f1, f2):
    lines1, lines2 = f1.splitlines(), f2.splitlines()
    diff = [i for i, (a, b) in enumerate(zip(lines1, lines2)) if a != b]
    offset = min(diff)
    static = "\n".join(lines1[:offset])
    flame1 = "\n".join(lines1[offset:])
    flame2 = "\n".join(lines2[offset:])
    return static, flame1, flame2, offset


async def animate_spaceship(canvas, start_row, start_col, f1, f2):
    max_rows, max_cols = canvas.getmaxyx()
    static, flame1, flame2, flame_offset = split_frames(f1, f2)
    row, col = start_row, start_col
    height, width = get_frame_size(f1)

    flame_cycle = itertools.cycle([flame1, flame1, flame2, flame2])

    for current_flame in flame_cycle:
        draw_frame(canvas, row, col, static, negative=True)
        draw_frame(canvas, row + flame_offset, col, flame1, negative=True)
        draw_frame(canvas, row + flame_offset, col, flame2, negative=True)

        dr, dc, _ = read_controls(canvas)
        row = max(0, min(row + dr, max_rows - height))
        col = max(0, min(col + dc, max_cols - width))

        draw_frame(canvas, row, col, static)
        draw_frame(canvas, row + flame_offset, col, current_flame)

        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    h, w = canvas.getmaxyx()

    with open("frames/rocket_frame_1.txt") as f:
        f1 = f.read()
    with open("frames/rocket_frame_2.txt") as f:
        f2 = f.read()

    coroutines = [
        blink(
            canvas,
            random.randint(1, h - 2),
            random.randint(1, w - 2),
            random.choice(STAR_SYMBOLS),
            offset_ticks=random.randint(1, 20),
        )
        for _ in range(80)
    ]

    start_r, start_c = h // 2, w // 2
    coroutines.append(animate_spaceship(canvas, start_r, start_c, f1, f2))

    try:
        while True:
            for coroutine in coroutines.copy():
                try:
                    coroutine.send(None)
                except StopIteration:
                    coroutines.remove(coroutine)
            canvas.refresh()
            time.sleep(TIC_TIMEOUT)
            if len(coroutines) == 0:
                break
    except KeyboardInterrupt:
        pass


def main():
    curses.wrapper(draw)


if __name__ == "__main__":
    main()