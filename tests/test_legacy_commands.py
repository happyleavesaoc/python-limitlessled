import unittest

from limitlessled.group.commands.legacy import (
    CommandLegacy,
    CommandSetLegacy,
    CommandSetRgbwLegacy,
    CommandSetWhiteLegacy,
)


class TestLegacyCommands(unittest.TestCase):
    def setUp(self):
        self.commands = CommandSetLegacy(1, 10)

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
        self.commands = CommandSetWhiteLegacy(1)

    def test_on(self):
        self.assertEqual(self.commands.on(), CommandLegacy(0x38, None, 1))

    def test_off(self):
        self.assertEqual(self.commands.off(), CommandLegacy(0x3B, None, 1))

    def test_night_light(self):
        sc = CommandLegacy(0x3B, None, 1)
        self.assertEqual(
            self.commands.night_light(),
            CommandLegacy(0xBB, None, 1, select=True, select_command=sc),
        )

    def test_dimmer(self):
        sc = CommandLegacy(0x38, None, 1)
        self.assertEqual(
            self.commands.dimmer(), CommandLegacy(0x34, None, 1, select=True, select_command=sc)
        )

    def test_brighter(self):
        sc = CommandLegacy(0x38, None, 1)
        self.assertEqual(
            self.commands.brighter(), CommandLegacy(0x3C, None, 1, select=True, select_command=sc)
        )

    def test_cooler(self):
        sc = CommandLegacy(0x38, None, 1)
        self.assertEqual(
            self.commands.cooler(), CommandLegacy(0x3F, None, 1, select=True, select_command=sc)
        )

    def test_warmer(self):
        sc = CommandLegacy(0x38, None, 1)
        self.assertEqual(
            self.commands.warmer(), CommandLegacy(0x3E, None, 1, select=True, select_command=sc)
        )


class TestRgbwLegacyCommands(unittest.TestCase):
    def setUp(self):
        self.commands = CommandSetRgbwLegacy(1)

    def test_on(self):
        self.assertEqual(self.commands.on(), CommandLegacy(0x45, None, 1))

    def test_off(self):
        self.assertEqual(self.commands.off(), CommandLegacy(0x46, None, 1))

    def test_night_light(self):
        sc = CommandLegacy(0x46, None, 1)
        self.assertEqual(
            self.commands.night_light(),
            CommandLegacy(0xC6, None, 1, select=True, select_command=sc),
        )

    def test_white(self):
        sc = CommandLegacy(0x45, None, 1)
        self.assertEqual(
            self.commands.white(), CommandLegacy(0xC5, None, 1, select=True, select_command=sc)
        )

    def test_hue(self):
        sc = CommandLegacy(0x45, None, 1)
        self.assertEqual(
            self.commands.hue(0.0), CommandLegacy(0x40, 0xAA, 1, select=True, select_command=sc)
        )
        self.assertEqual(
            self.commands.hue(0.5), CommandLegacy(0x40, 0x2A, 1, select=True, select_command=sc)
        )

    def test_brightness(self):
        sc = CommandLegacy(0x45, None, 1)
        self.assertEqual(
            self.commands.brightness(0.0),
            CommandLegacy(0x4E, 0x02, 1, select=True, select_command=sc),
        )
        self.assertEqual(
            self.commands.brightness(0.5),
            CommandLegacy(0x4E, 0x0F, 1, select=True, select_command=sc),
        )
        self.assertEqual(
            self.commands.brightness(1.0),
            CommandLegacy(0x4E, 0x1B, 1, select=True, select_command=sc),
        )
