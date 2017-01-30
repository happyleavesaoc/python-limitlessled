""" Utility functions. """

from colorsys import rgb_to_hsv, hsv_to_rgb

from limitlessled import Color


def hue_of_color(color):
    """
    Gets the hue of a color.
    :param color: The RGB color tuple.
    :return: The hue of the color (0.0-1.0).
    """
    return rgb_to_hsv(*color)[0]


def saturation_of_color(color):
    """
    Gets the saturation of a color.
    :param color: The RGB color tuple.
    :return: The saturation of the color (0.0-1.0).
    """
    return rgb_to_hsv(*color)[1]


def to_rgb(hue, saturation):
    """
    Converts hue and saturation to RGB color.
    :param hue: The hue of the color.
    :param saturation: The saturation of the color.
    :return: The RGB color tuple.
    """
    return Color(*hsv_to_rgb(hue, saturation, 1))


def transition(value, maximum, start, end):
    """ Transition between two values.

    :param value: Current iteration.
    :param maximum: Maximum number of iterations.
    :param start: Start value.
    :param end: End value.
    :returns: Transitional value.
    """
    return round(start + (end - start) * value / maximum, 2)


def steps(current, target, max_steps):
    """ Steps between two values.

    :param current: Current value (0.0-1.0).
    :param target: Target value (0.0-1.0).
    :param max_steps: Maximum number of steps.
    """
    return int(abs((current * max_steps) - (target * max_steps)))
