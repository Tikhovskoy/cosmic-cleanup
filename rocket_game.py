import asyncio
import curses
import random
import time
import itertools

from curses_helpers import draw_frame, get_frame_size, read_controls
from physics import update_speed
from obstacles import Obstacle, show_obstacles
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics

TIC_TIMEOUT = 0.1
STAR_SYMBOLS = "+*.:"

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
year = 1957


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def show_year_and_phrases(canvas):
    while True:
        phrase = PHRASES.get(year, "")
        year_text = f"Year: {year}"
        
        canvas.addstr(1, 1, year_text)
        if phrase:
            canvas.addstr(2, 1, phrase)
        else:
            canvas.addstr(2, 1, " " * 50)
            
        await asyncio.sleep(0)


async def advance_year():
    global year
    while True:
        await sleep(15)
        year += 1


async def show_gameover(canvas):
    gameover_text = r"""
 ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
    """

    rows, columns = canvas.getmaxyx()
    text_lines = gameover_text.strip().split('\n')
    
    center_row = rows // 2 - len(text_lines) // 2
    
    while True:
        for i, line in enumerate(text_lines):
            center_column = columns // 2 - len(line) // 2
            canvas.addstr(center_row + i, max(0, center_column), line[:columns-1])
        
        await asyncio.sleep(0)


async def blink(canvas, row, col, symbol="*", offset_ticks=1):
    while True:
        canvas.addstr(row, col, symbol, curses.A_DIM)
        await sleep(offset_ticks)
        canvas.addstr(row, col, symbol)
        await sleep(3)
        canvas.addstr(row, col, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, col, symbol)
        await sleep(3)


def split_frames(f1, f2):
    lines1, lines2 = f1.splitlines(), f2.splitlines()
    diff = [i for i, (a, b) in enumerate(zip(lines1, lines2)) if a != b]
    offset = min(diff)
    static = "\n".join(lines1[:offset])
    flame1 = "\n".join(lines1[offset:])
    flame2 = "\n".join(lines2[offset:])
    return static, flame1, flame2, offset


async def animate_spaceship(canvas, start_row, start_col, f1, f2):
    global obstacles
    max_rows, max_cols = canvas.getmaxyx()
    static, flame1, flame2, flame_offset = split_frames(f1, f2)
    row, col = start_row, start_col
    height, width = get_frame_size(f1)
    row_speed = col_speed = 0

    flame_cycle = itertools.cycle([flame1, flame1, flame2, flame2])

    for current_flame in flame_cycle:
        draw_frame(canvas, row, col, static, negative=True)
        draw_frame(canvas, row + flame_offset, col, flame1, negative=True)
        draw_frame(canvas, row + flame_offset, col, flame2, negative=True)

        dr, dc, space_pressed = read_controls(canvas)
        row_speed, col_speed = update_speed(row_speed, col_speed, dr, dc)
        
        if space_pressed:
            coroutines.append(fire(canvas, row, col + width // 2))
        
        row += row_speed
        col += col_speed
        
        row = max(0, min(row, max_rows - height))
        col = max(0, min(col, max_cols - width))

        for obstacle in obstacles:
            if obstacle.has_collision(row, col, height, width):
                coroutines.append(show_gameover(canvas))
                return

        draw_frame(canvas, row, col, static)
        draw_frame(canvas, row + flame_offset, col, current_flame)

        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    global obstacles, obstacles_in_last_collisions
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                obstacles_in_last_collisions.append(obstacle)
                return
        
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    global obstacles, obstacles_in_last_collisions
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    rows_size, columns_size = get_frame_size(garbage_frame)
    
    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles.append(obstacle)
    
    try:
        while row < rows_number:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                center_row = row + rows_size / 2
                center_column = column + columns_size / 2
                coroutines.append(explode(canvas, center_row, center_column))
                return
                
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
            
            obstacle.row = row
            obstacle.column = column
    finally:
        if obstacle in obstacles:
            obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas):
    garbage_files = [
        "frames/duck.txt",
        "frames/hubble.txt", 
        "frames/lamp.txt",
        "frames/trash_large.txt",
        "frames/trash_small.txt",
        "frames/trash_xl.txt"
    ]
    
    _, columns_number = canvas.getmaxyx()
    
    while True:
        delay_tics = get_garbage_delay_tics(year)
        
        if delay_tics is None:
            await sleep(1)
            continue
            
        garbage_file = random.choice(garbage_files)
        with open(garbage_file) as f:
            garbage_frame = f.read()
        
        column = random.randint(0, columns_number - 1)
        coroutines.append(fly_garbage(canvas, column, garbage_frame, speed=0.5))
        
        await sleep(delay_tics)


def draw(canvas):
    global coroutines, obstacles, obstacles_in_last_collisions, year
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
    coroutines.append(fill_orbit_with_garbage(canvas))
    coroutines.append(show_obstacles(canvas, obstacles))
    coroutines.append(show_year_and_phrases(canvas))
    coroutines.append(advance_year())

    try:
        while True:
            for coroutine in coroutines.copy():
                try:
                    coroutine.send(None)
                except StopIteration:
                    if coroutine in coroutines:
                        coroutines.remove(coroutine)
                except GeneratorExit:
                    if coroutine in coroutines:
                        coroutines.remove(coroutine)
                except Exception:
                    if coroutine in coroutines:
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