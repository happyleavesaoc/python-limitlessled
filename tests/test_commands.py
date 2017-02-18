import unittest
from limitlessled.bridge import Bridge
from limitlessled.group.white import WHITE
from limitlessled.group.rgbw import RGBW
from limitlessled.group.commands import Command, CommandSet, command_set_factory
from limitlessled.group.commands.legacy import CommandSetWhiteLegacy, CommandSetRgbwLegacy


class TestLegacyCommandSetFactory(unittest.TestCase):

    def setUp(self):
        self.bridge = Bridge('localhost', 9999, version=5)

    def test_legacy_white_command_set_factory(self):
        self.assertTrue(isinstance(command_set_factory(self.bridge, 1, WHITE), CommandSetWhiteLegacy))

    def test_legacy_rgbw_command_set_factory(self):
        self.assertTrue(isinstance(command_set_factory(self.bridge, 1, RGBW), CommandSetRgbwLegacy))

    def test_bad_command_set_factory(self):
        with self.assertRaises(ValueError):
            command_set_factory(self.bridge, 1, 'bad')


class TestCommand(unittest.TestCase):

    def setUp(self):
        self.command = Command(b'\x00\x00', 1, select=True, select_command=None)

    def test_bytes(self):
        self.assertEqual(self.command.bytes, b'\x00\x00')

    def test_group_number(self):
        self.assertEqual(self.command.group_number, 1)

    def test_select(self):
        self.assertEqual(self.command.select, True)

    def test_select_command(self):
        self.assertEqual(self.command.select_command, None)


class TestCommandSet(unittest.TestCase):

    def setUp(self):
        self.commandset = CommandSet(None, 1, 10)

    def test_brightness_steps(self):
        self.assertEqual(self.commandset.brightness_steps, 10)

    def test_hue_steps(self):
        self.assertEqual(self.commandset.hue_steps, 1)

    def test_saturation_steps(self):
        self.assertEqual(self.commandset.saturation_steps, 1)

    def test_temperature_steps(self):
        self.assertEqual(self.commandset.temperature_steps, 1)
