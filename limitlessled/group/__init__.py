""" LimitlessLED groups. """

import math
import time
import threading
import queue

from limitlessled import MIN_WAIT, REPS
from limitlessled.pipeline import Pipeline, PipelineQueue
from limitlessled.group.commands import command_set_factory


def rate(wait=MIN_WAIT, reps=REPS):
    """ Rate limit a command function.

    :param wait: How long to wait between commands.
    :param reps: How many times to send a command.
    :returns: Decorator.
    """
    def decorator(function):
        """ Decorator function.

        :returns: Wrapper.
        """
        def wrapper(self, *args, **kwargs):
            """ Wrapper.

            :param args: Passthrough positional arguments.
            :param kwargs: Passthrough keyword arguments.
            """
            saved_wait = self.wait
            saved_reps = self.reps
            self.wait = wait
            self.reps = reps
            function(self, *args, **kwargs)
            self.wait = saved_wait
            self.reps = saved_reps
        return wrapper
    return decorator


class Group(object):
    """ LimitlessLED group. """

    def __init__(self, bridge, number, name, led_type):
        """ Initialize group.

        :param bridge: Member of this bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        :param led_type: The type of the led.
        """
        self.name = name
        self.number = number
        self._bridge = bridge
        self._index = number - 1
        self._command_set = command_set_factory(bridge, number, led_type)
        self._on = False
        self._brightness = 0.5
        self._queue = queue.Queue()
        self._event = threading.Event()
        self._thread = PipelineQueue(self._queue, self._event)
        self._thread.daemon = True
        self._thread.start()
        self.wait = MIN_WAIT
        self.reps = REPS

    @property
    def on(self):
        """ Is the group on?

        :return: True if the group is on, otherwise False.
        """
        return self._on

    @on.setter
    def on(self, state):
        """ Turn on or off.

        :param state: True (on) or False (off).
        """
        self._on = state
        cmd = self.command_set.off()
        if state:
            cmd = self.command_set.on()
        self.send(cmd)

    @property
    def bridge(self):
        """ Bridge property. """
        return self._bridge

    @property
    def command_set(self):
        """Command set property. """
        return self._command_set

    def flash(self, duration=0.0):
        """ Flash a group.

        :param duration: How quickly to flash (in seconds).
        """
        for _ in range(2):
            self.on = not self.on
            time.sleep(duration)

    def send(self, cmd):
        """ Send a command to the bridge.

        :param cmd: List of command bytes.
        """
        self._bridge.send(cmd, wait=self.wait, reps=self.reps)

    def enqueue(self, pipeline):
        """ Start a pipeline.

        :param pipeline: Start this pipeline.
        """
        copied = Pipeline().append(pipeline)
        copied.group = self
        self._queue.put(copied)

    def stop(self):
        """ Stop a running pipeline. """
        self._event.set()

    def _wait(self, duration, steps, commands):
        """ Compute wait time.

        :param duration: Total time (in seconds).
        :param steps: Number of steps.
        :param commands: Number of commands.
        :returns: Wait in seconds.
        """
        wait = ((duration - self.wait * self.reps * commands) / steps) - \
               (self.wait * self.reps * self._bridge.active)
        return max(0, wait)

    def _scale_steps(self, duration, commands, *steps):
        """ Scale steps

        :param duration: Total time (in seconds)
        :param commands: Number of commands to be executed.
        :param steps: Steps for one or many properties to take.
        :return: Steps scaled to time and total.
        """
        factor = duration / ((self.wait * self.reps * commands) - \
                 (self.wait * self.reps * self._bridge.active))
        steps = [math.ceil(factor * step) for step in steps]
        if len(steps) == 1:
            return steps[0]
        else:
            return steps

    def __str__(self):
        """ String representation.

        :returns: String
        """
        return '{} ({}) @ {}'.format(self.number, self.name, self._bridge.ip)
