""" Command sets for wifi bridge version 5 and lower. """

import math

from limitlessled.group.rgbw import RGBW
from limitlessled.group.white import WHITE
from limitlessled.group.commands import CommandSet, Command


class CommandLegacy(Command):
    """ Represents a single v6 command to be sent to the bridge. """

    SUFFIX_BYTE = 0x00
    BRIDGE_SHORT_VERSION_MIN = 3
    BRIDGE_LONG_BYTE = 0x55

    def __init__(self, cmd_1, cmd_2, group_number,
                 select=False, select_command=None):
        """
        Initialize command.
        :param cmd_1: The first part of the command.
        :param cmd_1: The second part of the command.
        :param group_number: Group number (1-4).
        :param select: If command requires selection.
        :param select_command: Selection command bytes.
        """
        super().__init__(cmd_1, cmd_2, group_number, select, select_command)

    def get_bytes(self, bridge):
        """
        Gets the full command as bytes.
        :param bridge: The bridge, to which the command should be sent.
        """
        if self.cmd_2 is not None:
            cmd = [self.cmd_1, self.cmd_2]
        else:
            cmd = [self.cmd_1, self.SUFFIX_BYTE]

        if bridge.version < self.BRIDGE_SHORT_VERSION_MIN:
            cmd.append(self.BRIDGE_LONG_BYTE)

        return bytearray(cmd)


class CommandSetLegacy(CommandSet):
    """ Base command set for legacy wifi bridges. """

    SUPPORTED_VERSIONS = [1, 2, 3, 4, 5]
    BRIGHTNESS_OFFSET = 2

    def convert_brightness(self, brightness):
        """
        Convert the brightness from decimal percent (0.0-1.0)
        to byte representation for use in commands.
        :param brightness: The brightness from in decimal percent (0.0-1.0).
        :return: The brightness in byte representation.
        """
        brightness = math.ceil(brightness * self.brightness_steps)
        return brightness + self.BRIGHTNESS_OFFSET

    @staticmethod
    def convert_hue(hue):
        """
        Converts the hue from HSV color circle to the LimitlessLED color wheel.
        :param hue: The hue in decimal percent (0.0-1.0).
        :return: The hue regarding the LimitlessLED color wheel.
        """
        hue = hue * -1 + 1 + (2.0/3.0)  # RGB -> BGR

        return int(math.floor((hue % 1) * 256))

    def _build_command(self, cmd_1, cmd_2=None,
                       select=False, select_command=None):
        """
        Constructs the complete command.
        :param cmd_1: Light command 1.
        :param cmd_2: Light command 2.
        :param select: If command requires selection.
        :param select_command: Selection command bytes.
        :return: The complete command.
        """

        return CommandLegacy(cmd_1, cmd_2,
                             self._group_number, select, select_command)


class CommandSetWhiteLegacy(CommandSetLegacy):
    """ Command set for white led light connected to legacy wifi bridge. """

    SUPPORTED_LED_TYPES = [WHITE]
    ON_BYTES = [0x38, 0x3D, 0x37, 0x32]
    OFF_BYTES = [0x3B, 0x33, 0x3A, 0x36]
    NIGHT_BYTES = [0xBB, 0xB3, 0xBA, 0xB6]
    BRIGHTNESS_STEPS = 10
    TEMPERATURE_STEPS = 10

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.BRIGHTNESS_STEPS,
                         temperature_steps=self.TEMPERATURE_STEPS)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(self.ON_BYTES[self._group_number - 1])

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(self.OFF_BYTES[self._group_number - 1])

    def night_light(self):
        """
        Build command for turning the led to night light mode.
        :return: The command.
        """
        return self._build_command(self.NIGHT_BYTES[self._group_number - 1],
                                   select=True, select_command=self.off())

    def dimmer(self):
        """
        Build command for setting the brightness one step dimmer.
        :return: The command.
        """
        return self._build_command(0x34, select=True, select_command=self.on())

    def brighter(self):
        """
        Build command for setting the brightness one step brighter.
        :return: The command.
        """
        return self._build_command(0x3C, select=True, select_command=self.on())

    def cooler(self):
        """
        Build command for setting the temperature one step cooler.
        :return: The command.
        """
        return self._build_command(0x3F, select=True, select_command=self.on())

    def warmer(self):
        """
        Build command for setting the temperature one step warmer.
        :return: The command.
        """
        return self._build_command(0x3E, select=True, select_command=self.on())


class CommandSetRgbwLegacy(CommandSetLegacy):
    """ Command set for RGBW led light connected to legacy wifi bridge. """

    SUPPORTED_LED_TYPES = [RGBW]
    HUE_STEPS = 255
    BRIGHTNESS_STEPS = 25

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.BRIGHTNESS_STEPS,
                         hue_steps=self.HUE_STEPS)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(self._offset(0x45))

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(self._offset(0x46))

    def night_light(self):
        """
        Build command for turning the led to night light mode.
        :return: The command.
        """
        return self._build_command(self._offset(0xC6),
                                   select=True, select_command=self.off())

    def white(self):
        """
        Build command for turning the led into white mode.
        :return: The command.
        """
        return self._build_command(self._offset(0xC5),
                                   select=True, select_command=self.on())

    def hue(self, hue):
        """
        Build command for setting the hue of the led.
        :param hue: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x40, self.convert_hue(hue),
                                   select=True, select_command=self.on())

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the led.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x4E, self.convert_brightness(brightness),
                                   select=True, select_command=self.on())

    def _offset(self, byte):
        """ Calcuate group command offset.

        :param byte: Base byte.
        :returns: Appropriate byte for group.
        """
        index = self._group_number - 1
        return byte + (index * 2)
