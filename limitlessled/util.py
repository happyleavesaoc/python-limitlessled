""" Utility functions. """

import math
from colorsys import rgb_to_hls


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
