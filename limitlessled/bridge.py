""" LimitlessLED Bridge. """

import queue
import socket
import time
import threading
from datetime import datetime, timedelta

from limitlessled import MIN_WAIT, REPS
from limitlessled.group.rgbw import RgbwGroup, RGBW, BRIDGE_LED
from limitlessled.group.rgbww import RgbwwGroup, RGBWW
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
KEEP_ALIVE_COMMAND_PREAMBLE = [0xD0, 0x00, 0x00, 0x00, 0x02]
KEEP_ALIVE_RESPONSE_PREAMBLE = [0xd8, 0x0, 0x0, 0x0, 0x07]
KEEP_ALIVE_TIME = 1
RECONNECT_TIME = 5
SOCKET_TIMEOUT = 5
STARTING_SEQUENTIAL_BYTE = 0x02


def group_factory(bridge, number, name, led_type):
    """ Make a group.

    :param bridge: Member of this bridge.
    :param number: Group number (1-4).
    :param name: Name of group.
    :param led_type: Either `RGBW`, `RGBWW`, `WHITE` or `BRIDGE_LED`.
    :returns: New group.
    """
    if led_type in [RGBW, BRIDGE_LED]:
        return RgbwGroup(bridge, number, name, led_type)
    elif led_type == RGBWW:
        return RgbwwGroup(bridge, number, name)
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
        self.is_closed = False
        self.wait = MIN_WAIT
        self.reps = REPS
        self.groups = []
        self.ip = ip
        self.version = version
        self._sn = STARTING_SEQUENTIAL_BYTE
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(SOCKET_TIMEOUT)
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
            self._init_connection()

            # Start keep alive thread.
            keep_alive_thread = threading.Thread(target=self._keep_alive)
            keep_alive_thread.daemon = True
            keep_alive_thread.start()

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

    def send(self, command, reps=REPS, wait=MIN_WAIT):
        """ Send a command to the physical bridge.

        :param command: A Command instance.
        :param reps: Number of repetitions.
        :param wait: Wait time in seconds.
        """
        # Enqueue the command.
        self._command_queue.put((command, reps, wait))
        # Wait before accepting another command.
        # This keeps individual groups relatively synchronized.
        sleep = reps * wait * self.active
        if command.select and self._selected_number != command.group_number:
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
        while not self.is_closed:
            # Get command from queue.
            (command, reps, wait) = self._command_queue.get()
            # Select group if a different group is currently selected.
            if command.select and self._selected_number != command.group_number:
                self._send_raw(command.select_command.bytes)
                time.sleep(SELECT_WAIT)
            # Repeat command as necessary.
            for _ in range(reps):
                self._send_raw(command.bytes)
                time.sleep(wait)
            self._selected_number = command.group_number

    def _send_raw(self, command):
        """
        Sends an raw command directly to the physical bridge.
        :param command: A bytearray.
        """
        self._socket.send(bytearray(command))
        self._sn = (self._sn + 1) % 256

    def _init_connection(self):
        """
        Requests the session ids of the bridge.
        :returns: True, if initialization was successful. False, otherwise.
        """
        try:
            response = bytearray(22)
            self._send_raw(BRIDGE_INITIALIZATION_COMMAND)
            self._socket.recv_into(response)
            self._wb1 = response[19]
            self._wb2 = response[20]
        except socket.timeout:
            return False

        return True

    def _reconnect(self):
        """
        Try continuously to reconnect to the bridge.
        """
        while not self.is_closed:
            if self._init_connection():
                return

            time.sleep(RECONNECT_TIME)

    def _keep_alive(self):
        """
        Send keep alive messages continuously to bridge.
        """
        while not self.is_closed:
            command = KEEP_ALIVE_COMMAND_PREAMBLE + [self.wb1, self.wb2]
            self._send_raw(command)

            start = datetime.now()
            connection_alive = False
            while datetime.now() - start < timedelta(seconds=SOCKET_TIMEOUT):
                response = bytearray(12)
                try:
                    self._socket.recv_into(response)
                except socket.timeout:
                    break

                if response[:5] == bytearray(KEEP_ALIVE_RESPONSE_PREAMBLE):
                    connection_alive = True
                    break

            if not connection_alive:
                self._reconnect()
                continue

            time.sleep(KEEP_ALIVE_TIME)

    def close(self):
        """
        Closes the connection to the bridge.
        """
        self.is_closed = True

