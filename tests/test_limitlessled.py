import unittest
from limitlessled import LimitlessLED
from limitlessled.bridge import Bridge
from limitlessled.group.white import WHITE


class TestLegacyLimitlessLED(unittest.TestCase):
    def setUp(self):
        self.ll = LimitlessLED()
        self.bridge = Bridge("localhost", 9999, version=5)
        self.group = self.bridge.add_group(1, "test", WHITE)

    def test_add_bridge(self):
        self.ll.add_bridge(self.bridge)

    def test_group(self):
        self.ll.add_bridge(self.bridge)
        self.assertEqual(self.ll.group("test"), self.group)
