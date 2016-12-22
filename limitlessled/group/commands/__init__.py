""" LimtlessLED command sets. """


def command_set_factory(bridge, group_number, led_type):
    """
    Create command set for controlling a specific led group.
    :param bridge: The bridge the leds are connected to.
    :param group_number: The group number.
    :param led_type: The type of the leds.
    :return: The created command set.
    """
    from limitlessled.group.commands.legacy import (
        CommandSetWhiteLegacy, CommandSetRgbwLegacy)
    from limitlessled.group.commands.v6 import (
        CommandSetBridgeLightV6, CommandSetWhiteV6,
        CommandSetRgbwV6, CommandSetRgbwwV6)

    command_sets = [CommandSetWhiteLegacy, CommandSetRgbwLegacy,
                    CommandSetBridgeLightV6, CommandSetWhiteV6,
                    CommandSetRgbwV6, CommandSetRgbwwV6]
    try:
        cls = next(cs for cs in command_sets if
                   bridge.version in cs.SUPPORTED_VERSIONS and
                   led_type in cs.SUPPORTED_LED_TYPES)
        return cls(bridge, group_number)
    except StopIteration:
        raise ValueError('There is no command set for '
                         'specified bridge version and led type.')


class CommandSet:
    """ Base class for command sets."""

    def __init__(self, bridge, group_number,
                 brightness_steps, color_steps=1, temperature_steps=1):
        """
        Initializes the command set.
        :param bridge: The bridge the leds are connected to.
        :param group_number: The group number.
        :param brightness_steps: The number of brightness steps.
        :param color_steps: The number of color steps.
        :param temperature_steps: The number of temperature steps.
        """
        self._bridge = bridge
        self._group_number = group_number
        self._brightness_steps = brightness_steps
        self._color_steps = color_steps
        self._temperature_steps = temperature_steps

    @property
    def brightness_steps(self):
        """
        Brightness steps property.
        :return: The number of brightness steps.
        """
        return self._brightness_steps

    @property
    def color_steps(self):
        """
        Color steps property.
        :return: The number of color steps.
        """
        return self._color_steps

    @property
    def temperature_steps(self):
        """
        Temperature steps property.
        :return: The number of temperature steps.
        """
        return self._temperature_steps
