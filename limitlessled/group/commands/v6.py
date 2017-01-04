""" Command sets for wifi bridge version 6. """


import math

from limitlessled.group.rgbw import RGBW, BRIDGE_LED
from limitlessled.group.rgbww import RGBWW
from limitlessled.group.white import WHITE
from limitlessled.group.commands import CommandSet, Command


class CommandSetV6(CommandSet):
    """ Base command set for wifi bridge v6. """

    SUPPORTED_VERSIONS = [6]
    PASSWORD_BYTE1 = 0x00
    PASSWORD_BYTE2 = 0x00
    MAX_HUE = 0xFF
    MAX_SATURATION = 0x64
    MAX_BRIGHTNESS = 0x64
    MAX_TEMPERATURE = 0x64

    def __init__(self, bridge, group_number, remote_style,
                 brightness_steps=None, hue_steps=None,
                 saturation_steps=None, temperature_steps=None):
        """
        Initialize the command set.
        :param bridge: The bridge the leds are connected to.
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
        super().__init__(bridge, group_number, brightness_steps,
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

    def _build_command(self, cmd_1, cmd_2):
        """
        Constructs the complete command.
        :param cmd_1: Light command 1.
        :param cmd_2: Light command 2.
        :return: The complete command.
        """
        wb1 = self._bridge.wb1
        wb2 = self._bridge.wb2
        sn = self._bridge.sn

        preamble = [0x80, 0x00, 0x00, 0x00, 0x11, wb1, wb2, 0x00, sn, 0x00]
        cmd = [0x31, self.PASSWORD_BYTE1, self.PASSWORD_BYTE2,
               self._remote_style, cmd_1, cmd_2, cmd_2, cmd_2, cmd_2]
        zone_selector = [self._group_number, 0x00]
        checksum = sum(cmd + zone_selector) & 0xFF

        return Command(preamble + cmd + zone_selector + [checksum],
                       self._group_number)


class CommandSetBridgeLightV6(CommandSetV6):
    """ Command set for bridge light of wifi bridge v6. """

    SUPPORTED_LED_TYPES = [BRIDGE_LED]
    REMOTE_STYLE = 0x00

    def __init__(self, bridge, group_number):
        """
        Initializes the command set.
        :param bridge: The bridge the leds are connected to.
        :param group_number: The group number.
        """
        super().__init__(bridge, group_number, self.REMOTE_STYLE)

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
    REMOTE_STYLE = 0x08

    def __init__(self, bridge, group_number):
        """
        Initializes the command set.
        :param bridge: The bridge the leds are connected to.
        :param group_number: The group number.
        """
        super().__init__(bridge, group_number, self.REMOTE_STYLE)

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
        return self._build_command(0x05, temperature)


class CommandSetRgbwV6(CommandSetV6):
    """ Command set for RGBW led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [RGBW]
    REMOTE_STYLE = 0x07

    def __init__(self, bridge, group_number):
        """
        Initializes the command set.
        :param bridge: The bridge the leds are connected to.
        :param group_number: The group number.
        """
        super().__init__(bridge, group_number, self.REMOTE_STYLE)

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


class CommandSetRgbwwV6(CommandSetV6):
    """ Command set for RGBWW led light connected to wifi bridge v6. """

    SUPPORTED_LED_TYPES = [RGBWW]
    REMOTE_STYLE = 0x08

    def __init__(self, bridge, group_number):
        """
        Initializes the command set.
        :param bridge: The bridge the leds are connected to.
        :param group_number: The group number.
        """
        super().__init__(bridge, group_number, self.REMOTE_STYLE)

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

    def white(self):
        """
        Build command for turning the led into white mode.
        :return: The command.
        """
        return self._build_command(0x05, 0x64)

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
