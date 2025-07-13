from limitlessled import Color
from limitlessled.bridge import Bridge
from limitlessled.group.rgbcct import RGBCCT
from limitlessled.group.rgbw import RGBW
from limitlessled.group.rgbww import RGBWW
from limitlessled.group.white import WHITE
from limitlessled.pipeline import Pipeline

bridge = Bridge("<your bridge ip address>")
bedroom = bridge.add_group(1, "bedroom", RGBW)
# A group number can support two groups as long as the types differ
bathroom = bridge.add_group(2, "bathroom", WHITE)
living_room = bridge.add_group(2, "living_room", RGBW)
kitchen = bridge.add_group(2, "kitchen", RGBWW)
# RGBCCT supports up to 8 zones (groups)
office = bridge.add_group(6, "office", RGBCCT)

selected = office
commands = (
    Pipeline()
    .off()
    .wait(3)
    .on()
    .brightness(0.7)
    .color(0, 0, 255)
    .transition(3, color=Color(255, 0, 0))
)
selected.enqueue(commands)
bridge.finish()
