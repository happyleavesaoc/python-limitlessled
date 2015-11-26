""" LimitlessLED.

http://www.limitlessled.com
"""

import logging
from collections import namedtuple

_LOGGER = logging.getLogger(__name__)


# Various constants.
MIN_WAIT = 0.1
REPS = 3
MAX_GROUPS = 4


# Color tuple.
Color = namedtuple("Color", "R G B")


class LimitlessLED(object):
    """ Represents a LimitlessLED installation. """
    def __init__(self):
        """ Initialize. """
        self._groups = {}

    def group(self, name):
        """ Fetch a named group.

        :param name: Name of group.
        :returns: Group.
        """
        return self._groups[name]

    def add_bridge(self, bridge):
        """ Add bridge groups.

        :param bridge: Add groups from this bridge.
        """
        for group in bridge.groups:
            self._groups[group.name] = group
