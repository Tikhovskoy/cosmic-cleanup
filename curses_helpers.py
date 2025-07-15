SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas):
    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        key = canvas.getch()
        if key == -1:
            break
        if key == UP_KEY_CODE:
            rows_direction = -1
        elif key == DOWN_KEY_CODE:
            rows_direction = 1
        elif key == LEFT_KEY_CODE:
            columns_direction = -1
        elif key == RIGHT_KEY_CODE:
            columns_direction = 1
        elif key == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_col, text, negative=False):
    max_rows, max_cols = canvas.getmaxyx()
    for dr, line in enumerate(text.splitlines()):
        row = round(start_row) + dr
        if row < 0 or row >= max_rows:
            continue
        for dc, ch in enumerate(line):
            col = round(start_col) + dc
            if col < 0 or col >= max_cols:
                continue
            if ch == " ":
                continue
            if row == max_rows - 1 and col == max_cols - 1:
                continue
            canvas.addch(row, col, " " if negative else ch)


def get_frame_size(text):
    lines = text.splitlines()
    return len(lines), max(map(len, lines))
