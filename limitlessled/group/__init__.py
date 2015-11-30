""" LimitlessLED groups. """

import math
import time
import threading
import queue

from limitlessled import MIN_WAIT
from limitlessled.pipeline import Pipeline, PipelineQueue


def rate(wait=MIN_WAIT, reps=None):
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

    def __init__(self, bridge, number, name):
        """ Initialize group.

        :param bridge: Member of this bridge.
        :param number: Group number (1-4).
        :param name: Group name.
        """
        self.name = name
        self.number = number
        self._bridge = bridge
        self._index = number - 1
        self._on = False
        self._brightness = 0.5
        self._queue = queue.Queue()
        self._event = threading.Event()
        self._thread = PipelineQueue(self._queue, self._event)
        self._thread.daemon = True
        self._thread.start()
        self.wait = MIN_WAIT

    @property
    def on(self):
        """ Is the group on?

        :return: True if the group is on, otherwise False.
        """
        return self._on

    @property
    def bridge(self):
        """ Bridge property. """
        return self._bridge

    def flash(self, duration=0.0):
        """ Flash a group.

        :param duration: How quickly to flash (in seconds).
        """
        for _ in range(2):
            self.on = not self.on
            time.sleep(duration)

    def send(self, cmd, select=False):
        """ Send a command to the bridge.

        :param cmd: List of command bytes.
        :param select: If command requires selection.
        """
        self._bridge.send(self, cmd, wait=self.wait,
                          reps=self.bridge.reps, select=select)

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

    def _wait(self, duration, commands):
        """ Compute wait time.

        :param duration: Total time (in seconds).
        :param commands: Number of commands.
        :returns: Wait in seconds.
        """
        wait = (duration / commands) - \
               (self.wait * self.bridge.reps * self._bridge.active)
        if wait < 0:
            wait = 0
        return wait

    def _scaled_steps(self, duration, steps, total):
        """ Scale steps.

        :param duration: Total time (in seconds).
        :param steps: Ideal step amount.
        :param total: Total steps to take.
        :returns: Steps scaled to time and total.
        """
        return math.ceil(duration /
                         (self.wait * self.bridge.reps * self._bridge.active) *
                         (steps / total))

    def __str__(self):
        """ String representation.

        :returns: String
        """
        return '{} ({}) @ {}'.format(self.number, self.name, self._bridge.ip)
