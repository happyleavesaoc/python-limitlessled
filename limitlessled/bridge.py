""" LimitlessLED Bridge. """

import queue
import socket
import time
import threading

from limitlessled import MIN_WAIT, REPS
from limitlessled.group.rgbw import RgbwGroup, RGBW, RGBWW, BRIDGE_LED
from limitlessled.group.white import WhiteGroup, WHITE


BRIDGE_PORT = 5987
BRIDGE_VERSION = 6
BRIDGE_LED_GROUP = 1
BRIDGE_LED_NAME = 'bridge'
SELECT_WAIT = 0.025
BRIDGE_INITIALIZATION_COMMAND = [0x20, 0x00, 0x00, 0x00, 0x16, 0x02, 0x62,
                                 0x3a, 0xd5, 0xed, 0xa3, 0x01, 0xae, 0x08,
                                 0x2d, 0x46, 0x61, 0x41, 0xa7, 0xf6, 0xdc,
                                 0xaf, 0xfe, 0xf7, 0x00, 0x00, 0x1e]
STARTING_SEQUENTIAL_BYTE = 0x02


def group_factory(bridge, number, name, led_type):
    """ Make a group.

    :param bridge: Member of this bridge.
    :param number: Group number (1-4).
    :param name: Name of group.
    :param led_type: Either `RGBW`, `RGBWW`, `WHITE` or `BRIDGE_LED`.
    :returns: New group.
    """
    if led_type in [RGBW, RGBWW, BRIDGE_LED]:
        return RgbwGroup(bridge, number, name, led_type)
    elif led_type == WHITE:
        return WhiteGroup(bridge, number, name)
    else:
        raise ValueError('Invalid LED type: %s', led_type)


class Bridge(object):
    """ Represents a LimitlessLED bridge. """

    def __init__(self, ip, port=BRIDGE_PORT, version=BRIDGE_VERSION,
                 bridge_led_name=BRIDGE_LED_NAME):
        """ Initialize bridge.

        Bridge version 6 (latest as of this release)
        can use the default parameters. For lower versions,
        use port 8899 (3 to 5) or 50000 (lower then 3).
        Lower versions also require sending a larger payload
        to the bridge (slower).

        :param ip: IP address of bridge.
        :param port: Bridge port.
        :param version: Bridge version.
        :param bridge_led_name: Name of the bridge led group.
        """
        self.wait = MIN_WAIT
        self.reps = REPS
        self.groups = []
        self.ip = ip
        self.version = version
        self._sn = STARTING_SEQUENTIAL_BYTE
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.connect((ip, port))
        self._command_queue = queue.Queue()
        self._lock = threading.Lock()
        self.active = 0
        self._selected_number = None

        # Start queue consumer thread.
        consumer = threading.Thread(target=self._consume)
        consumer.daemon = True
        consumer.start()

        # Version specific stuff
        self._wb1 = None
        self._wb2 = None
        self._bridge_led = None
        if self.version >= 6:
            # Create bridge led group
            self._bridge_led = group_factory(self, BRIDGE_LED_GROUP,
                                             bridge_led_name, BRIDGE_LED)

            # Initialize connection to retrieve bridge session ids (wb1, wb2)
            response = bytearray(22)
            self._send_raw(BRIDGE_INITIALIZATION_COMMAND, response)
            self._wb1 = response[19]
            self._wb2 = response[20]

    @property
    def sn(self):
        """ Gets the current sequential byte. """
        return self._sn

    @property
    def wb1(self):
        """ Gets the bridge session id 1. """
        return self._wb1

    @property
    def wb2(self):
        """ Gets the bridge session id 2. """
        return self._wb2

    @property
    def bridge_led(self):
        """ Get the group to control the bridge led. """
        return self._bridge_led

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

    def send(self, group, command, reps=REPS, wait=MIN_WAIT, select=False):
        """ Send a command to the physical bridge.

        :param group: Run on this group.
        :param command: A bytearray.
        :param reps: Number of repetitions.
        :param wait: Wait time in seconds.
        :param select: Select group if necessary.
        """
        # TODO select depending on version?
        # Enqueue the command.
        self._command_queue.put((group, command, reps, wait, select))
        # Wait before accepting another command.
        # This keeps individual groups relatively synchronized.
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
            (group, command, reps, wait, select) = self._command_queue.get()
            # Select group if a different group is currently selected.
            if select and group and self._selected_number != group.number:
                self._send_raw(group.get_select_cmd())
                time.sleep(SELECT_WAIT)
            # Repeat command as necessary.
            for _ in range(reps):
                self._send_raw(command)
                time.sleep(wait)
            self._selected_number = group.number

    def _send_raw(self, command, recv_buffer=None):
        """
        Sends an raw command directly to the physical bridge.
        :param command: A bytearray.
        :param recv_buffer: Response buffer. If None, no response is received.
        """
        self._socket.send(bytearray(command))
        self._sn += 1

        if recv_buffer:
            self._socket.recv_into(recv_buffer)

