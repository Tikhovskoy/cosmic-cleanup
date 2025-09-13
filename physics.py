import math


def _limit(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _apply_acceleration(speed, speed_limit, forward=True):
    speed_limit = abs(speed_limit)

    speed_fraction = speed / speed_limit

    delta = math.cos(speed_fraction) * 0.75

    if forward:
        result_speed = speed + delta
    else:
        result_speed = speed - delta

    result_speed = _limit(result_speed, -speed_limit, speed_limit)

    if abs(result_speed) < 0.1:
        result_speed = 0

    return result_speed


def update_speed(row_speed, column_speed, rows_direction, columns_direction, row_speed_limit=2, column_speed_limit=2, fading=0.8):
    if rows_direction not in (-1, 0, 1):
        raise ValueError(f'Wrong rows_direction value {rows_direction}. Expects -1, 0 or 1.')

    if columns_direction not in (-1, 0, 1):
        raise ValueError(f'Wrong columns_direction value {columns_direction}. Expects -1, 0 or 1.')
    
    if fading < 0 or fading > 1:
        raise ValueError(f'Wrong columns_direction value {fading}. Expects float between 0 and 1.')
        

    row_speed *= fading
    column_speed *= fading

    row_speed_limit, column_speed_limit = abs(row_speed_limit), abs(column_speed_limit)

    if rows_direction != 0:
        row_speed = _apply_acceleration(row_speed, row_speed_limit, rows_direction > 0)

    if columns_direction != 0:
        column_speed = _apply_acceleration(column_speed, column_speed_limit, columns_direction > 0)

    return row_speed, column_speed