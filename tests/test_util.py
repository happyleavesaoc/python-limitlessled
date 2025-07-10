import unittest
from limitlessled import util, Color


class TestUtil(unittest.TestCase):
    def test_hue_of_color(self):
        red = Color(255, 0, 0)
        self.assertEqual(util.hue_of_color(red), 0.0)

    def test_saturation_of_color(self):
        red = Color(255, 0, 0)
        self.assertEqual(util.saturation_of_color(red), 1.0)

    def test_to_rgb(self):
        _red = Color(255, 0, 0)
        # TODO: resolve correct values
        # self.assertEqual(util.to_rgb(0, 1), red)

    def test_transition(self):
        self.assertEqual(util.transition(0, 100, 0, 10), 0.0)
        self.assertEqual(util.transition(1, 100, 0, 10), 0.1)
        self.assertEqual(util.transition(10, 100, 0, 10), 1.0)
        self.assertEqual(util.transition(100, 100, 0, 10), 10.0)

    def test_steps(self):
        self.assertEqual(util.steps(0, 1.0, 100), 100)
        self.assertEqual(util.steps(0.5, 1.0, 100), 50)
        self.assertEqual(util.steps(1.0, 1.0, 100), 0)
        with self.assertRaises(ValueError):
            util.steps(-1, 1.0, 100)
        with self.assertRaises(ValueError):
            util.steps(0, 2.0, 100)
