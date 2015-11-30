""" LimitlessLED Bridge. """

import queue
import socket
import time
import threading

from limitlessled import MIN_WAIT, DEFAULT_REPS
from limitlessled.group.rgbw import RgbwGroup, RGBW
from limitlessled.group.white import WhiteGroup, WHITE


BRIDGE_PORT = 8899
BRIDGE_VERSION = 5
BRIDGE_SHORT_VERSION_MIN = 3
BRIDGE_LONG_BYTE = 0x55
SELECT_WAIT = 0.025
DEFAULT_PRIORITY = 10


def group_factory(bridge, number, name, led_type):
    """ Make a group.

    :param bridge: Member of this bridge.
    :param number: Group number (1-4).
    :param name: Name of group.
    :param led_type: Either `RGBW` or `WHITE`.
    :returns: New group.
    """
    if led_type == RGBW:
        return RgbwGroup(bridge, number, name)
    elif led_type == WHITE:
        return WhiteGroup(bridge, number, name)
    else:
        raise ValueError('Invalid LED type: %s', led_type)


class Bridge(object):
    """ Represents a LimitlessLED bridge. """

    def __init__(self, ip, port=BRIDGE_PORT, version=BRIDGE_VERSION, 
            reps=DEFAULT_REPS):
        """ Initialize bridge.

        Bridge version 3 through 5 (latest as of this release)
        can use the default parameters. For lower versions,
        use port 50000. Lower versions also require sending a
        larger payload to the bridge (slower).

        :param ip: IP address of bridge.
        :param port: Bridge port.
        :param version: Bridge version.
        """
        self.wait = MIN_WAIT
        self.reps = reps
        self.groups = []
        self.ip = ip
        self.version = version
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.connect((ip, port))
        self._command_queue = queue.PriorityQueue()
        self._lock = threading.Lock()
        self.active = 0
        self._selected_number = None
        self._seqnum = 0
        # Start queue consumer thread.
        consumer = threading.Thread(target=self._consume)
        consumer.daemon = True
        consumer.start()

    def incr_active(self):
        """ Increment number of active groups. """
        with self._lock:
            self.active += 1

    def decr_active(self):
        """ Decrement number of active groups. """
        with self._lock:
            self.active -= 1

    def add_group(self, number, name, led_type):
        """ Add a group.

        :param number: Group number (1-4).
        :param name: Group name.
        :param led_type: Either `RGBW` or `WHITE`.
        :returns: Added group.
        """
        group = group_factory(self, number, name, led_type)
        self.groups.append(group)
        return group

    def send(self, group, command, reps=None, wait=MIN_WAIT, select=False, 
            priority=DEFAULT_PRIORITY):
        """ Send a command to the physical bridge.

        :param group: Run on this group.
        :param command: A bytearray.
        :param reps: Number of repetitions.
        :param wait: Wait time in seconds.
        :param select: Select group if necessary.
        """
        if reps is None:
            reps = self.reps
            
        seqnum = self._seqnum
        self._seqnum += 1
        # Enqueue the command.
        self._command_queue.put((priority, seqnum, group, command, reps, wait, 
                                 select))
        # Wait before accepting another command.
        # This keeps indvidual groups relatively synchronized.
        sleep = reps * wait * self.active
        if select and self._selected_number != group.number:
            sleep += SELECT_WAIT
        time.sleep(sleep)

    def _consume(self):
        """ Consume commands from the queue.

        The command is repeated according to the configured value.
        Wait after each command is sent.

        The bridge socket is a shared resource. It must only
        be used by one thread at a time. Note that this can and
        will delay commands if multiple groups are attempting
        to communicate at the same time on the same bridge.

        TODO: Only wait when another command comes in.
        """
        while True:
            # Get command from queue.
            (priority, seqnum, group, command, reps, wait, select) = \
                self._command_queue.get()
            # Select group if a different group is currently selected.
            if select and self._selected_number != group.number:
                self._socket.send(bytearray(group.get_select_cmd()))
                time.sleep(SELECT_WAIT)
            # Repeat command as necessary.
            for _ in range(reps):
                if self.version < BRIDGE_SHORT_VERSION_MIN:
                    command.append(BRIDGE_LONG_BYTE)
                self._socket.send(bytearray(command))
                time.sleep(wait)
            self._selected_number = group.number
