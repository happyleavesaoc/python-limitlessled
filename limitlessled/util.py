""" Utility functions. """

import math
from colorsys import rgb_to_hls


def rgb_to_hue(red, green, blue):
    """ Convert RGB color to hue value.

    0% lightness or 100% lightness (white & black),
    (255, 255, 255) & (0,0,0) aren't representable.

    Also note that the LimitlessLED color spectrum
    starts at blue.

    :param red: Red value (0-255).
    :param green: Green value (0-255).
    :param blue: Blue value (0-255).
    :returns: Hue value (0-255).
    """
    hue = rgb_to_hls(red / 255, green / 255, blue / 255)[0] \
        * -1 \
        + 1 \
        + (2.0/3.0)  # RGB -> BGR
    return int(math.floor((hue % 1) * 256))


def transition(value, maximum, start, end):
    """ Transition between two values.

    :param value: Current iteration.
    :param maximum: Maximum number of iterations.
    :param start: Start value.
    :param end: End value.
    :returns: Transitional value.
    """
    return round(start + (end - start) * value / maximum, 2)


def transition3(value, maximum, start, end):
    """ Transition three values.

    :param value: Current iteration.
    :param maximum: Maximum number of iterations.
    :param start: Start tuple.
    :param end: End tuple.
    :returns: Transitional tuple.
    """
    return (
        transition(value, maximum, start[0], end[0]),
        transition(value, maximum, start[1], end[1]),
        transition(value, maximum, start[2], end[2])
    )


def steps(current, target, max_steps):
    """ Steps between two values.

    :param current: Current value (0.0-1.0).
    :param target: Target value (0.0-1.0).
    :param max_steps: Maximum number of steps.
    """
    return int(abs((current * max_steps) - (target * max_steps)))
