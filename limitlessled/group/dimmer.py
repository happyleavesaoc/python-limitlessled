""" Dimmer controller LimitlessLED group. """

import time

from limitlessled import util
from limitlessled.group import Group, rate
from limitlessled.util import steps

DIMMER = 'dimmer'


class DimmerGroup(Group):
    """ Dimmer LimitlessLED group. """

    def __init__(self, bridge, number, name):
        """ Initialize dimmer group.

        Brightness must be initialized
        to some value.

        :param bridge: Associated bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        """
        super().__init__(bridge, number, name, DIMMER)

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

    def transition(self, duration, brightness=None):
        """ Transition wrapper.

        Short-circuit transition if necessary.

        :param duration: Duration of transition.
        :param brightness: Transition to this brightness.
        """
        if duration == 0:
            if brightness is not None:
                self.brightness = brightness
            return
        if brightness != self.brightness:
            self._transition(duration, brightness)

    @rate(reps=1)
    def _transition(self, duration, brightness):
        """ Complete a transition.

        :param duration: Duration of transition.
        :param brightness: Transition to this brightness.
        """
        # Set initial value.
        b_start = self.brightness
        # Compute ideal step amount.
        b_steps = 0
        if brightness is not None:
            b_steps = steps(self.brightness, brightness,
                            self.command_set.brightness_steps)
        # Compute ideal step amount (at least one).
        # Calculate wait.
        wait = self._wait(duration, b_steps, b_steps)
        # Scale down steps if no wait time.
        if wait == 0:
            b_steps = self._scale_steps(duration, b_steps,
                                                 b_steps)
        # Perform transition.
        for i in range(b_steps):
            # Brightness.
            if b_steps > 0:
                self.brightness = util.transition(i, b_steps,
                                                  b_start, brightness)
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

    def _brighter(self):
        """ One step brighter. """
        self.send(self.command_set.brighter())

    def _dimmer(self):
        """ One step dimmer. """
        self.send(self.command_set.dimmer())
