from limitlessled import Color
from limitlessled.group import Group
from limitlessled.group.rgbww import RgbwwGroup
from limitlessled.util import rgb_to_hsv

RGBCCT = "rgbcct"
RGB_WHITE = Color(255, 255, 255)


class RgbcctGroup(RgbwwGroup):
    """RGBCCT LimitlessLED group."""

    def __init__(self, bridge, number, name):
        """Initialize RGBCCT group.

        :param bridge: Associated bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        """
        Group.__init__(self, bridge, number, name, RGBCCT)
        self._saturation = 0
        self._hue = 0
        self._temperature = 0.5
        self._color = RGB_WHITE

    def white(self):
        """Set color to white."""
        self._color = RGB_WHITE
        cmd = self.command_set.white()
        self.send(cmd)

    @property
    def color(self):
        """Color property.

        :returns: Color.
        """
        return self._color

    @color.setter
    def color(self, color):
        """Set group color.

        Color is set on a best-effort basis.

        :param color: RGB color tuple.
        """
        self.hue, self.saturation, self.brightness = rgb_to_hsv(*[x / 255 for x in color])
