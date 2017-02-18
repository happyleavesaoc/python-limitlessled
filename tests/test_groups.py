import unittest
from limitlessled.bridge import Bridge
from limitlessled.group.white import WhiteGroup, WHITE
from limitlessled.group.rgbw import RgbwGroup, RGBW
from limitlessled.group.rgbww import RgbwwGroup, RGBWW


# TODO: mock socket
class TestWhiteGroup(unittest.TestCase):

    def setUp(self):
        self.bridge = Bridge('localhost', 9999, version=5)

    def test_brightness(self):
        pass

    def test_temperature(self):
        pass

    def test_transition(self):
        pass

    def tearDown(self):
        self.bridge.close()
