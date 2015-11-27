""" White LimitlessLED group. """

import time

from limitlessled import util
from limitlessled.group import Group, rate
from limitlessled.util import steps

WHITE = 'white'
STEPS = 10
ON_BYTES = [0x38, 0x3D, 0x37, 0x32]
OFF_BYTES = [0x3B, 0x33, 0x3A, 0x36]


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
        super().__init__(bridge, number, name)
        self._temperature = 0.5

    @property
    def on(self):
        """ On/off property.

        :returns: On/off state.
        """
        return super(WhiteGroup, self).on

    @on.setter
    def on(self, state):
        """ Turn on or off.

        :param state: True (on) or False (off).
        """
        self._on = state
        byte = OFF_BYTES
        if state:
            byte = ON_BYTES
        cmd = [byte[self._index], 0x00]
        self.send(cmd)

    def get_select_cmd(self):
        """ Get selection command bytes. """
        return [ON_BYTES[self._index], 0x00]

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
        self._setter('_temperature', temperature,
                     self._coolest, self._warmest,
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
            b_steps = steps(self.brightness, brightness, STEPS)
        t_steps = 0
        if temperature is not None:
            t_steps = steps(self.temperature, temperature, STEPS)
        total = b_steps + t_steps
        # Compute wait.
        wait = self._wait(duration, total)
        # Scale down steps if no wait time.
        if wait == 0:
            b_steps = self._scaled_steps(duration, b_steps, total)
            t_steps = self._scaled_steps(duration, t_steps, total)
            total = b_steps + t_steps
        # Perform transition.
        j = 0
        for i in range(total):
            # Brightness.
            if b_steps > 0 and i % (total / b_steps) == 0:
                j += 1
                self.brightness = util.transition(j, b_steps,
                                                  b_start, brightness)
            # Temperature.
            elif t_steps > 0:
                self.temperature = util.transition(i - j + 1, t_steps,
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
                       self._dimmer, self._brighter)

    def _to_temperature(self, temperature):
        """ Step to a given temperature.

        :param temperature: Get to this temperature.
        """
        self._to_value(self._temperature, temperature,
                       self._cooler, self._warmer)

    @rate(reps=1)
    def _to_value(self, current, target, step_down, step_up):
        """ Step to a value

        :param current: Current value.
        :param target: Target value.
        :param step_down: Down function.
        :param step_up: Up function.
        """
        for _ in range(steps(current, target, STEPS)):
            if (current - target) > 0:
                step_down()
            else:
                step_up()

    @rate(wait=0.025, reps=2)
    def _brightest(self):
        """ Group as bright as possible. """
        for _ in range(steps(self.brightness, 1.0, STEPS)):
            self._brighter()

    @rate(wait=0.025, reps=2)
    def _dimmest(self):
        """ Group brightness as dim as possible. """
        for _ in range(steps(self.brightness, 0.0, STEPS)):
            self._dimmer()

    @rate(wait=0.025, reps=2)
    def _warmest(self):
        """ Group temperature as warm as possible. """
        for _ in range(steps(self.temperature, 1.0, STEPS)):
            self._warmer()

    @rate(wait=0.025, reps=2)
    def _coolest(self):
        """ Group temperature as cool as possible. """
        for _ in range(steps(self.temperature, 0.0, STEPS)):
            self._cooler()

    def _brighter(self):
        """ One step brighter. """
        self.send([0x3C, 0x00], select=True)

    def _dimmer(self):
        """ One step dimmer. """
        self.send([0x34, 0x00], select=True)

    def _warmer(self):
        """ One step warmer. """
        self.send([0x3E, 0x00], select=True)

    def _cooler(self):
        """ One step cooler. """
        self.send([0x3F, 0x00], select=True)
