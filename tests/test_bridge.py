import unittest

from limitlessled.bridge import Bridge, group_factory
from limitlessled.group.rgbw import RGBW, RgbwGroup
from limitlessled.group.white import WHITE, WhiteGroup


class TestGroupFactory(unittest.TestCase):
    def test_legacy_group_factory(self):
        bridge = Bridge("localhost", 9999, version=5)
        white_group = group_factory(bridge, 1, "test", WHITE)
        self.assertTrue(isinstance(white_group, WhiteGroup))
        rgbw_group = group_factory(bridge, 2, "test", RGBW)
        self.assertTrue(isinstance(rgbw_group, RgbwGroup))
        bridge.close()


class TestLegacyBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge("localhost", 9999, version=5)

    def test_add_group(self):
        group = self.bridge.add_group(1, "test", WHITE)
        self.assertTrue(isinstance(group, WhiteGroup))

    def tearDown(self):
        self.bridge.close()
        self.assertTrue(self.bridge.is_closed)
