import unittest

from limitlessled.bridge import Bridge


# TODO: mock socket
class TestWhiteGroup(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge("localhost", 9999, version=5)

    def test_brightness(self):
        pass

    def test_temperature(self):
        pass

    def test_transition(self):
        pass

    def tearDown(self):
        self.bridge.close()
