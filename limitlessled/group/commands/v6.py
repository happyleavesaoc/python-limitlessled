""" Command sets for wifi bridge version 6. """


import math

from limitlessled.group.rgbw import RGBW, BRIDGE_LED
from limitlessled.group.rgbww import RGBWW
from limitlessled.group.wrgb import WRGB
from limitlessled.group.white import WHITE
from limitlessled.group.dimmer import DIMMER
from limitlessled.group.commands import CommandSet, Command


class CommandV6(Command):
    """ Represents a single v6 command to be sent to the bridge. """

    PASSWORD_BYTE1 = 0x00
    PASSWORD_BYTE2 = 0x00

    def __init__(self, cmd_1, cmd_2, remote_style, group_number,
                 select=False, select_command=None):
        """
        Initialize command.
        :param cmd_1: The first part of the command.
        :param cmd_1: The second part of the command.
        :param remote_style: The remote style of the led.
        :param group_number: Group number (1-4).
        :param select: If command requires selection.
        :param select_command: Selection command bytes.
        """
        super().__init__(cmd_1, cmd_2, group_number, select, select_command)
        self._remote_style = remote_style

    def get_bytes(self, bridge):
        """
        Gets the full command as bytes.
        :param bridge: The bridge, to which the command should be sent.
        """
        if not bridge.is_ready:
            raise Exception('The bridge has to be ready to construct command.')

        wb1 = bridge.wb1
        wb2 = bridge.wb2
        sn = bridge.sn

        preamble = [0x80, 0x00, 0x00, 0x00, 0x11, wb1, wb2, 0x00, sn, 0x00]
        cmd = [0x31, self.PASSWORD_BYTE1, self.PASSWORD_BYTE2,
               self._remote_style, self._cmd_1,
               self._cmd_2, self._cmd_2, self._cmd_2, self._cmd_2]
        zone_selector = [self._group_number, 0x00]
        checksum = sum(cmd + zone_selector) & 0xFF

        return bytearray(preamble + cmd + zone_selector + [checksum])


class CommandSetV6(CommandSet):
    """ Base command set for wifi bridge v6. """

    SUPPORTED_VERSIONS = [6]
    MAX_HUE = 0xFF
    MAX_SATURATION = 0x64
    MAX_BRIGHTNESS = 0x64
    MAX_TEMPERATURE = 0x64

    def __init__(self, group_number, remote_style,
                 brightness_steps=None, hue_steps=None,
                 saturation_steps=None, temperature_steps=None):
        """
        Initialize the command set.
        :param group_number: The group number.
        :param remote_style: The remote style of the device to control.
        :param brightness_steps: The number of brightness steps.
        :param hue_steps: The number of color steps.
        :param saturation_steps: The number of saturation steps
        :param temperature_steps: The number of temperature steps.
        """
        brightness_steps = brightness_steps or self.MAX_BRIGHTNESS + 1
        hue_steps = hue_steps or self.MAX_HUE + 1
        saturation_steps = saturation_steps or self.MAX_SATURATION + 1
        temperature_steps = temperature_steps or self.MAX_TEMPERATURE + 1
        super().__init__(group_number, brightness_steps,
                         hue_steps=hue_steps,
                         saturation_steps=saturation_steps,
                         temperature_steps=temperature_steps)
        self._remote_style = remote_style

    def convert_brightness(self, brightness):
        """
        Convert the brightness from decimal percent (0.0-1.0)
        to byte representation for use in commands.
        :param brightness: The brightness from in decimal percent (0.0-1.0).
        :return: The brightness in byte representation.
        """
        return math.ceil(brightness * self.MAX_BRIGHTNESS)

    def convert_saturation(self, saturation):
        """
        Convert the saturation from decimal percent (0.0-1.0)
        to byte representation for use in commands.
        :param saturation: The saturation from in decimal percent (0.0-1.0).
        1.0 is the maximum saturation where no white leds will be on. 0.0 is no
        saturation.
        :return: The saturation in byte representation.
        """

        saturation_inverted = 1 - saturation
        return math.ceil(saturation_inverted * self.MAX_SATURATION)

    def convert_temperature(self, temperature):
        """
        Convert the temperature from decimal percent (0.0-1.0)
        to byte representation for use in commands.
        :param temperature: The temperature from in decimal percent (0.0-1.0).
        :return: The temperature in byte representation.
        """
        return math.ceil(temperature * self.MAX_TEMPERATURE)

    def convert_hue(self, hue, legacy_color_wheel=False):
        """
        Converts the hue from HSV color circle to the LimitlessLED color wheel.
        :param hue: The hue in decimal percent (0.0-1.0).
        :param legacy_color_wheel: Whether or not use the old color wheel.
        :return: The hue regarding the LimitlessLED color wheel.
        """
        hue = math.ceil(hue * self.MAX_HUE)
        if legacy_color_wheel:
            hue = (176 - hue) % (self.MAX_HUE + 1)
            hue = (self.MAX_HUE - hue - 0x37) % (self.MAX_HUE + 1)
        else:
            hue += 10  # The color wheel for RGBWW bulbs seems to be shifted

        return hue % (self.MAX_HUE + 1)

    def _build_command(self, cmd_1, cmd_2,
                       select=False, select_command=None):
        """
        Constructs the complete command.
        :param cmd_1: Light command 1.
        :param cmd_2: Light command 2.
        :return: The complete command.
        """

        return CommandV6(cmd_1, cmd_2, self._remote_style, self._group_number,
                         select, select_command)


class CommandSetBridgeLightV6(CommandSetV6):
    """ Command set for bridge light of wifi bridge v6. """

    SUPPORTED_LED_TYPES = [BRIDGE_LED]
    REMOTE_STYLE = 0x00

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(0x03, 0x03)

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(0x03, 0x04)

    def white(self):
        """
        Build command for turning the led into white mode.
        :return: The command.
        """
        return self._build_command(0x03, 0x05)

    def hue(self, hue):
        """
        Build command for setting the hue of the led.
        :param hue: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x01, self.convert_hue(hue))

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the led.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x02, self.convert_brightness(brightness))


class CommandSetWhiteV6(CommandSetV6):
    """ Command set for white led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [WHITE]
    REMOTE_STYLE = 0x01

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(0x01, 0x07)

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(0x01, 0x08)

    def night_light(self):
        """
        Build command for turning the led into night light mode.
        :return: The command.
        """
        return self._build_command(0x01, 0x06)

    def dimmer(self):
        """
        Build command for setting the brightness one step dimmer.
        :return: The command.
        """
        return self._build_command(0x01, 0x02, select=True, select_command=self.on())

    def brighter(self):
        """
        Build command for setting the brightness one step brighter.
        :return: The command.
        """
        return self._build_command(0x01, 0x01, select=True, select_command=self.on())

    def cooler(self):
        """
        Build command for setting the temperature one step cooler.
        :return: The command.
        """
        return self._build_command(0x01, 0x04, select=True, select_command=self.on())

    def warmer(self):
        """
        Build command for setting the temperature one step warmer.
        :return: The command.
        """
        return self._build_command(0x01, 0x03, select=True, select_command=self.on())

class CommandSetDimmerV6(CommandSetV6):
    """ Command set for Dimmer LED dimmer (1CH MiLight dimmer) connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [DIMMER]
    REMOTE_STYLE = 0x03

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the dimmer on.
        :return: The command.
        """
        return self._build_command(0x04, 0x03)

    def off(self):
        """
        Build command for turning the dimmer off.
        :return: The command.
        """
        return self._build_command(0x04, 0x04)

    def night_light(self):
        """
        Build command for turning the dimmer into night light mode.
        :return: The command.
        """
        return self._build_command(0x04, 0x02)

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the controller.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x01, self.convert_brightness(brightness))

class CommandSetRgbwV6(CommandSetV6):
    """ Command set for RGBW led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [RGBW]
    REMOTE_STYLE = 0x07

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(0x03, 0x01)

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(0x03, 0x02)

    def night_light(self):
        """
        Build command for turning the led into night light mode.
        :return: The command.
        """
        return self._build_command(0x03, 0x06)

    def white(self):
        """
        Build command for turning the led into white mode.
        :return: The command.
        """
        return self._build_command(0x03, 0x05)

    def hue(self, hue):
        """
        Build command for setting the hue of the led.
        :param hue: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x01, self.convert_hue(hue, True))

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the led.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x02, self.convert_brightness(brightness))

class CommandSetWrgbV6(CommandSetV6):
    """ Command set for WRGB led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [WRGB]
    REMOTE_STYLE = 0x06

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(0x03, 0x01)

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(0x03, 0x02)

    def night_light(self):
        """
        Build command for turning the led into night light mode.
        :return: The command.
        """
        return self._build_command(0x03, 0x06)

    def white(self):
        """
        Build command for turning the led into white mode.
        :return: The command.
        """
        return self._build_command(0x03, 0x05)

    def white_up(self):
        """
        Build command for turning the white channel up
        :return: The command.
        """
        return self._build_command(0x03, 0x03)

    def white_down(self):
        """
        Build command for turning the white channel doen
        :return: The command.
        """
        return self._build_command(0x03, 0x04)

    def red_up(self):
        """
        Build command for turning the red channel up
        :return: The command.
        """
        return self._build_command(0x03, 0x05)

    def red_down(self):
        """
        Build command for turning the red channel doen
        :return: The command.
        """
        return self._build_command(0x03, 0x06)

    def green_up(self):
        """
        Build command for turning the green channel up
        :return: The command.
        """
        return self._build_command(0x03, 0x07)

    def green_down(self):
        """
        Build command for turning the green channel doen
        :return: The command.
        """
        return self._build_command(0x03, 0x08)

    def blue_up(self):
        """
        Build command for turning the blue channel up
        :return: The command.
        """
        return self._build_command(0x03, 0x09)

    def blue_down(self):
        """
        Build command for turning the blue channel doen
        :return: The command.
        """
        return self._build_command(0x03, 0x0A)

    def hue(self, hue):
        """
        Build command for setting the hue of the led.
        :param hue: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x01, self.convert_hue(hue, True))

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the led.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x02, self.convert_brightness(brightness))

class CommandSetRgbwwV6(CommandSetV6):
    """ Command set for RGBWW led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [RGBWW]
    REMOTE_STYLE = 0x08

    def __init__(self, group_number):
        """
        Initializes the command set.
        :param group_number: The group number.
        """
        super().__init__(group_number, self.REMOTE_STYLE)

    def on(self):
        """
        Build command for turning the led on.
        :return: The command.
        """
        return self._build_command(0x04, 0x01)

    def off(self):
        """
        Build command for turning the led off.
        :return: The command.
        """
        return self._build_command(0x04, 0x02)

    def night_light(self):
        """
        Build command for turning the led into night light mode.
        :return: The command.
        """
        return self._build_command(0x04, 0x05)

    def white(self, temperature=1):
        """
        Build command for turning the led into white mode.
        :param: The temperature to set.
        :return: The command.
        """
        return self.temperature(temperature)

    def hue(self, hue):
        """
        Build command for setting the hue of the led.
        :param hue: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x01, self.convert_hue(hue))

    def saturation(self, saturation):
        """
        Build command for setting the saturation of the led.
        :param saturation: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x02, self.convert_saturation(saturation))

    def brightness(self, brightness):
        """
        Build command for setting the brightness of the led.
        :param brightness: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x03, self.convert_brightness(brightness))

    def temperature(self, temperature):
        """
        Build command for setting the temperature of the led.
        :param temperature: Value to set (0.0-1.0).
        :return: The command.
        """
        return self._build_command(0x05, self.convert_temperature(temperature))
