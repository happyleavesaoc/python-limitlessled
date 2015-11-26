""" Various preset pipelines. """

from limitlessled import Color
from limitlessled.pipeline import Pipeline


# Alarm (flash red).
ALARM = Pipeline() \
    .on() \
    .color(255, 0, 0) \
    .flash() \
    .repeat()


# Color loop (R->G->B).
COLORLOOP = Pipeline() \
    .on() \
    .transition(10, color=Color(255, 0, 0)) \
    .transition(10, color=Color(0, 255, 0)) \
    .transition(10, color=Color(0, 0, 255)) \
    .repeat(stages=3)
