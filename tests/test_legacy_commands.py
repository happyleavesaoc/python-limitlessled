import unittest
from limitlessled.bridge import Bridge
from limitlessled.group.commands import Command
from limitlessled.group.commands.legacy import CommandSetLegacy, CommandSetWhiteLegacy, CommandSetRgbwLegacy


class TestLegacyCommands(unittest.TestCase):

    def setUp(self):
        bridge = Bridge('localhost', 9999, version=5)
        self.commands = CommandSetLegacy(bridge, 1, 10)

    def test_convert_brightness(self):
        self.assertEqual(self.commands.convert_brightness(0), 2)
        self.assertEqual(self.commands.convert_brightness(0.5), 7)
        self.assertEqual(self.commands.convert_brightness(1.0), 12)

    def test_convert_hue(self):
        self.assertEqual(CommandSetLegacy.convert_hue(0), 170)
        self.assertEqual(CommandSetLegacy.convert_hue(0.5), 42)
        self.assertEqual(CommandSetLegacy.convert_hue(1.0), 170)


class TestWhiteLegacyCommands(unittest.TestCase):

    def setUp(self):
        bridge = Bridge('localhost', 9999, version=5)
        self.commands = CommandSetWhiteLegacy(bridge, 1)

    def test_on(self):
        self.assertEqual(self.commands.on(), Command(b'\x38\x00', 1))

    def test_off(self):
        self.assertEqual(self.commands.off(), Command(b'\x3b\x00', 1))

    def test_dimmer(self):
        sc = Command(b'\x38\x00', 1)
        self.assertEqual(self.commands.dimmer(), Command(b'\x34\x00', 1, select=True, select_command=sc))

    def test_brighter(self):
        sc = Command(b'\x38\x00', 1)
        self.assertEqual(self.commands.brighter(), Command(b'\x3c\x00', 1, select=True, select_command=sc))

    def test_cooler(self):
        sc = Command(b'\x38\x00', 1)
        self.assertEqual(self.commands.cooler(), Command(b'\x3f\x00', 1, select=True, select_command=sc))

    def test_warmer(self):
        sc = Command(b'\x38\x00', 1)
        self.assertEqual(self.commands.warmer(), Command(b'\x3e\x00', 1, select=True, select_command=sc))


class TestRgbwLegacyCommands(unittest.TestCase):

    def setUp(self):
        bridge = Bridge('localhost', 9999, version=5)
        self.commands = CommandSetRgbwLegacy(bridge, 1)

    def test_on(self):
        self.assertEqual(self.commands.on(), Command(b'\x45\x00', 1))

    def test_off(self):
        self.assertEqual(self.commands.off(), Command(b'\x46\x00', 1))

    def test_white(self):
        sc = Command(b'\x45\x00', 1)
        self.assertEqual(self.commands.white(), Command(b'\xc5\x00', 1, select=True, select_command=sc))

    def test_hue(self):
        sc = Command(b'\x45\x00', 1)
        self.assertEqual(self.commands.hue(0.0), Command(b'\x40\xaa', 1, select=True, select_command=sc))
        self.assertEqual(self.commands.hue(0.5), Command(b'\x40\x2a', 1, select=True, select_command=sc))

    def test_brightness(self):
        sc = Command(b'\x45\x00', 1)
        self.assertEqual(self.commands.brightness(0.0), Command(b'\x4e\02', 1, select=True, select_command=sc))
        self.assertEqual(self.commands.brightness(0.5), Command(b'\x4e\x0f', 1, select=True, select_command=sc))
        self.assertEqual(self.commands.brightness(1.0), Command(b'\x4e\x1b', 1, select=True, select_command=sc))
