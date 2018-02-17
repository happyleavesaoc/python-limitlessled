""" White LimitlessLED group. """

import time

from limitlessled import util
from limitlessled.group import Group, rate
from limitlessled.util import steps

WHITE = 'white'


class WhiteGroup(Group):
    """ White LimitlessLED group. """

    def __init__(self, bridge, number, name):
        """ Initialize white group.

        Brightness and temperature must be initialized
        to some value.

        :param bridge: Associated bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        """
        super().__init__(bridge, number, name, WHITE)
        self._temperature = 0.5

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
        """ Set the brightness.

        :param brightness: Value to set (0.0-1.0).
        """
        try:
            cmd = self.command_set.brightness(brightness)
            self.send(cmd)
            self._brightness = brightness
        except AttributeError:
            self._setter('_brightness', brightness,
                         self._dimmest, self._brightest,
                         self._to_brightness)

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
        try:
            cmd = self.command_set.temperature(temperature)
            self.send(cmd)
            self._temperature = temperature
        except AttributeError:
            self._setter('_temperature', temperature,
                         self._warmest, self._coolest,
                         self._to_temperature)

    def transition(self, duration, brightness=None, temperature=None):
        """ Transition wrapper.

        Short-circuit transition if necessary.

        :param duration: Duration of transition.
        :param brightness: Transition to this brightness.
        :param temperature: Transition to this temperature.
        """
        # Transition immediately if duration is zero.
        if duration == 0:
            if brightness is not None:
                self.brightness = brightness
            if temperature is not None:
                self.temperature = temperature
            return
        if brightness != self.brightness or temperature != self.temperature:
            self._transition(duration, brightness, temperature)

    @rate(reps=1)
    def _transition(self, duration, brightness, temperature):
        """ Complete a transition.

        :param duration: Duration of transition.
        :param brightness: Transition to this brightness.
        :param temperature: Transition to this temperature.
        """
        # Set initial value.
        b_start = self.brightness
        t_start = self.temperature
        # Compute ideal step amount.
        b_steps = 0
        if brightness is not None:
            b_steps = steps(self.brightness, brightness,
                            self.command_set.brightness_steps)
        t_steps = 0
        if temperature is not None:
            t_steps = steps(self.temperature, temperature,
                            self.command_set.temperature_steps)
        # Compute ideal step amount (at least one).
        total_steps = max(b_steps, t_steps, 1)
        total_commands = b_steps + t_steps
        # Calculate wait.
        wait = self._wait(duration, total_steps, total_commands)
        # Scale down steps if no wait time.
        if wait == 0:
            b_steps, t_steps = self._scale_steps(duration, total_commands,
                                                 b_steps, t_steps)
            total_steps = max(b_steps, t_steps, 1)
        # Perform transition.
        for i in range(total_steps):
            # Brightness.
            if b_steps > 0 and i % (total_steps / b_steps) == 0:
                self.brightness = util.transition(i, total_steps,
                                                  b_start, brightness)
            # Temperature.
            elif t_steps > 0:
                self.temperature = util.transition(i, total_steps,
                                                   t_start, temperature)
            # Wait.
            time.sleep(wait)

    def _setter(self, attr, value, bottom, top, to_step):
        """ Set a value.

        :param attr: Attribute to set.
        :param value: Value to use.
        :param bottom: Get to bottom value.
        :param top: Get to top value.
        :param to_step: Get to intermediary value.
        """
        if value < 0 or value > 1:
            raise ValueError("out of range")
        if value == 0.0:
            bottom()
        elif value == 1.0:
            top()
        else:
            to_step(value)
        setattr(self, attr, value)

    def _to_brightness(self, brightness):
        """ Step to a given brightness.

        :param brightness: Get to this brightness.
        """
        self._to_value(self._brightness, brightness,
                       self.command_set.brightness_steps,
                       self._dimmer, self._brighter)

    def _to_temperature(self, temperature):
        """ Step to a given temperature.

        :param temperature: Get to this temperature.
        """
        self._to_value(self._temperature, temperature,
                       self.command_set.temperature_steps,
                       self._warmer, self._cooler)

    @rate(reps=1)
    def _to_value(self, current, target, max_steps, step_down, step_up):
        """ Step to a value

        :param current: Current value.
        :param target: Target value.
        :param max_steps: Maximum number of steps.
        :param step_down: Down function.
        :param step_up: Up function.
        """
        for _ in range(steps(current, target, max_steps)):
            if (current - target) > 0:
                step_down()
            else:
                step_up()

    @rate(wait=0.025, reps=2)
    def _brightest(self):
        """ Group as bright as possible. """
        for _ in range(steps(self.brightness, 1.0,
                             self.command_set.brightness_steps)):
            self._brighter()

    @rate(wait=0.025, reps=2)
    def _dimmest(self):
        """ Group brightness as dim as possible. """
        for _ in range(steps(self.brightness, 0.0,
                             self.command_set.brightness_steps)):
            self._dimmer()

    @rate(wait=0.025, reps=2)
    def _warmest(self):
        """ Group temperature as warm as possible. """
        for _ in range(steps(self.temperature, 0.0,
                             self.command_set.temperature_steps)):
            self._warmer()

    @rate(wait=0.025, reps=2)
    def _coolest(self):
        """ Group temperature as cool as possible. """
        for _ in range(steps(self.temperature, 1.0,
                             self.command_set.temperature_steps)):
            self._cooler()

    def _brighter(self):
        """ One step brighter. """
        self.send(self.command_set.brighter())

    def _dimmer(self):
        """ One step dimmer. """
        self.send(self.command_set.dimmer())

    def _warmer(self):
        """ One step warmer. """
        self.send(self.command_set.warmer())

    def _cooler(self):
        """ One step cooler. """
        self.send(self.command_set.cooler())
