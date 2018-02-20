""" RGBW LimitlessLED group. """

import math
import time

from limitlessled import Color, util
from limitlessled.group import Group, rate
from limitlessled.util import steps, hue_of_color, saturation_of_color, to_rgb


RGBWW = 'rgbww'
RGB_WHITE = Color(255, 255, 255)


class RgbwwGroup(Group):
    """ RGBW LimitlessLED group. """

    def __init__(self, bridge, number, name):
        """ Initialize RGBW group.

        :param bridge: Associated bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        """
        super().__init__(bridge, number, name, RGBWW)
        self._saturation = 0
        self._hue = 0
        self._temperature = 0.5
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
        self._color = color
        self.saturation = saturation_of_color(color)
        if self.saturation != 0:
            self.hue = hue_of_color(color)

    def white(self):
        """ Set color to white. """
        self._color = RGB_WHITE
        cmd = self.command_set.white(self.temperature)
        self.send(cmd)

    def night_light(self):
        """ Set night light mode. """
        cmd = self.command_set.night_light()
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
        self._update_color()
        cmd = self.command_set.hue(hue)
        self.send(cmd)

    @property
    def saturation(self):
        """ Saturation property.

        :returns: Saturation.
        """
        return self._saturation

    @saturation.setter
    def saturation(self, saturation):
        """ Set the group saturation.

        :param saturation: Saturation in decimal percent (0.0-1.0).
        """
        if saturation < 0 or saturation > 1:
            raise ValueError("Saturation must be a percentage "
                             "represented as decimal 0-1.0")
        self._saturation = saturation
        self._update_color()
        if saturation == 0:
            self.white()
        else:
            cmd = self.command_set.saturation(saturation)
            self.send(cmd)

    def _update_color(self):
        """ Update the color property from hue and saturation values.
        """
        self._color = to_rgb(self.hue, self.saturation)

    @property
    def temperature(self):
        """ Temperature property.

        :returns: Temperature (0.0-1.0)
        """
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """ Set the temperature.

        :param temperature: Value to set (0.0-1.0).
        """
        if temperature < 0 or temperature > 1:
            raise ValueError("Temperature must be a percentage "
                             "represented as decimal 0-1.0")
        self._temperature = temperature
        cmd = self.command_set.temperature(temperature)
        self.send(cmd)

    def transition(self, duration,
                   color=None, brightness=None, temperature=None):
        """ Transition wrapper.

        Short-circuit transition as necessary.

        :param duration: Time to transition.
        :param color: Transition to this color.
        :param brightness: Transition to this brightness.
        :param temperature: Transition to this temperature.
        """
        if color and temperature is not None:
            raise ValueError("Cannot transition to color and temperature "
                             "simultaneously.")

        # Transition to white immediately.
        if color == RGB_WHITE:
            self.white()
        # Transition away from white immediately.
        elif self.color == RGB_WHITE and color is not None:
            self.color = color
        # Transition immediately if duration is zero.
        if duration == 0:
            if brightness is not None:
                self.brightness = brightness
            if color:
                self.color = color
            if temperature is not None:
                self.temperature = temperature
            return
        # Perform transition
        if color and color != self.color:
            self._transition(duration, brightness,
                             hue=hue_of_color(color),
                             saturation=saturation_of_color(color))
        elif temperature != self.temperature:
            self._transition(duration, brightness, temperature=temperature)
        elif brightness != self.brightness:
            self._transition(duration, brightness)

    @rate(wait=0.025, reps=1)
    def _transition(self, duration, brightness,
                    hue=None, saturation=None, temperature=None):
        """ Transition.

        :param duration: Time to transition.
        :param brightness: Transition to this brightness.
        :param hue: Transition to this hue.
        :param saturation: Transition to this saturation.
        :param temperature: Transition to this temperature.
        """
        # Calculate brightness steps.
        b_steps = 0
        if brightness is not None:
            b_steps = steps(self.brightness,
                            brightness, self.command_set.brightness_steps)
            b_start = self.brightness
        # Calculate hue steps.
        h_steps = 0
        if hue is not None:
            h_steps = steps(self.hue,
                            hue, self.command_set.hue_steps)
            h_start = self.hue
        # Calculate saturation steps.
        s_steps = 0
        if saturation is not None:
            s_steps = steps(self.saturation,
                            saturation, self.command_set.saturation_steps)
            s_start = self.saturation
        # Calculate temperature steps.
        t_steps = 0
        if temperature is not None:
            t_steps = steps(self.temperature,
                            temperature, self.command_set.temperature_steps)
            t_start = self.temperature
        # Compute ideal step amount (at least one).
        total_steps = max(b_steps, h_steps, s_steps, t_steps, 1)
        total_commands = b_steps + h_steps + s_steps + t_steps
        # Calculate wait.
        wait = self._wait(duration, total_steps, total_commands)
        # Scale down steps if no wait time.
        if wait == 0:
            scaled_steps = self._scale_steps(duration, total_commands, b_steps,
                                             h_steps, s_steps, t_steps)
            b_steps, h_steps, s_steps, t_steps = scaled_steps
            total_steps = max(b_steps, h_steps, s_steps, t_steps, 1)
        # Perform transition.
        for i in range(total_steps):
            # Brightness.
            if b_steps > 0 and i % math.ceil(total_steps/b_steps) == 0:
                self.brightness = util.transition(i, total_steps,
                                                  b_start, brightness)
            # Hue.
            if h_steps > 0 and i % math.ceil(total_steps/h_steps) == 0:
                self.hue = util.transition(i, total_steps,
                                           h_start, hue)
            # Saturation.
            if s_steps > 0 and i % math.ceil(total_steps/s_steps) == 0:
                self.saturation = util.transition(i, total_steps,
                                                  s_start, saturation)
            # Temperature.
            if t_steps > 0 and i % math.ceil(total_steps/t_steps) == 0:
                self.temperature = util.transition(i, total_steps,
                                                   t_start, temperature)

            # Wait.
            time.sleep(wait)
