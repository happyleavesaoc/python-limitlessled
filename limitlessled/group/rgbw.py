""" RGBW LimitlessLED group. """

import math
import time

from colorsys import rgb_to_hsv, hsv_to_rgb

from limitlessled import Color, util
from limitlessled.group import Group, rate
from limitlessled.util import steps, hue_of_color


RGBW = 'rgbw'
BRIDGE_LED = 'bridge-led'
RGB_WHITE = Color(255, 255, 255)


class RgbwGroup(Group):
    """ RGBW LimitlessLED group. """

    def __init__(self, bridge, number, name, led_type=RGBW):
        """ Initialize RGBW group.

        :param bridge: Associated bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        :param led_type: The type of the led. (RGBW or BRIDGE_LED)
        """
        super().__init__(bridge, number, name, led_type)
        self._hue = 0
        self._color = RGB_WHITE

    @property
    def color(self):
        """ Color property.

        :returns: Color.
        """
        return self._color

    @color.setter
    def color(self, color):
        """ Set group color.

        Color is set on a best-effort basis.

        :param color: RGB color tuple.
        """
        if color == RGB_WHITE:
            self.white()
            return
        self.color = color
        self.hue = hue_of_color(color)

    def white(self):
        """ Set color to white. """
        self._color = RGB_WHITE
        cmd = self.command_set.white()
        self.send(cmd)

    @property
    def brightness(self):
        """ Brightness property.

        :returns: Brightness.
        """
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        """ Set the group brightness.

        :param brightness: Brightness in decimal percent (0.0-1.0).
        """
        if brightness < 0 or brightness > 1:
            raise ValueError("Brightness must be a percentage "
                             "represented as decimal 0-1.0")
        self._brightness = brightness
        cmd = self.command_set.brightness(brightness)
        self.send(cmd)

    @property
    def hue(self):
        """ Hue property.

        :returns: Hue.
        """
        return self._hue

    @hue.setter
    def hue(self, hue):
        """ Set the group hue.

        :param hue: Hue in decimal percent (0.0-1.0).
        """
        if hue < 0 or hue > 1:
            raise ValueError("Hue must be a percentage "
                             "represented as decimal 0-1.0")
        self._hue = hue
        cmd = self.command_set.hue(hue)
        self.send(cmd)

    def transition(self, duration, color=None, brightness=None):
        """ Transition wrapper.

        Short-circuit transition as necessary.

        :param duration: Time to transition.
        :param color: Transition to this color.
        :param brightness: Transition to this brightness.
        """
        # Transition to white immediately.
        if color == RGB_WHITE:
            self.white()
            color = None
        # Transition away from white immediately.
        elif self.color == RGB_WHITE and color is not None:
            self.color = color
            color = None
        # Transition immediately if duration is zero.
        if duration == 0:
            if color:
                self.color = color
            if brightness is not None:
                self.brightness = brightness
            return
        # Perform transition
        if color != self.color or brightness != self.brightness:
            if color is None and brightness == self.brightness:
                return
            self._transition(duration, color, brightness)

    @rate(wait=0.025, reps=1)
    def _transition(self, duration, color, brightness):
        """ Transition.

        :param duration: Time to transition.
        :param color: Transition to this color.
        :param brightness: Transition to this brightness.
        """
        # Calculate brightness steps.
        b_steps = 0
        if brightness is not None:
            b_steps = steps(self.brightness,
                            brightness, self.command_set.brightness_steps)
            b_start = self.brightness
        # Calculate color steps.
        c_steps = 0
        if color is not None:
            c_steps = abs(self.command_set.convert_hue(*self.color)
                          - self.command_set.convert_hue(*color))
            c_start = rgb_to_hsv(*self._color)
            c_end = rgb_to_hsv(*color)
        # Compute ideal step amount (at least one).
        total = max(c_steps + b_steps, 1)
        # Calculate wait.
        wait = self._wait(duration, total)
        # Scale down steps if no wait time.
        if wait == 0:
            total = self._scaled_steps(duration, total, total)
        # Perform transition.
        j = 0
        for i in range(total):
            # Brightness.
            if (b_steps > 0
                    and i % math.ceil(total/b_steps) == 0):
                j += 1
                self.brightness = util.transition(j, b_steps,
                                                  b_start, brightness)
            # Color.
            elif c_steps > 0:
                rgb = hsv_to_rgb(*util.transition3(i - j + 1,
                                                   total - b_steps,
                                                   c_start, c_end))
                self.color = Color(*rgb)
            # Wait.
            time.sleep(wait)
