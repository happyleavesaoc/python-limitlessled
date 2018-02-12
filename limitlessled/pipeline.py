""" LimitlessLED pipeline. """

import logging
import threading
import time

from limitlessled import Color

_LOGGER = logging.getLogger(__name__)


class PipelineQueue(threading.Thread):
    """ Pipeline queue. """

    def __init__(self, queue, event):
        """ Initialize pipeline queue.

        :param queue: Read from this queue.
        :param event: Read from this event.
        """
        super(PipelineQueue, self).__init__()
        self._queue = queue
        self._event = event

    def run(self):
        """ Run the pipeline queue.

        The pipeline queue will run forever.
        """
        while True:
            self._event.clear()
            self._queue.get().run(self._event)


class Stage(object):
    """ Stage. """

    def __init__(self, name, args, kwargs):
        """ Initialize stage.

        :param name: Name of stage.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        """
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        """ String representation of Stage.

        :returns: String
        """
        args = []
        if len(self.args) > 0:
            args += ['{}'.format(a) for a in self.args]
        if len(self.kwargs) > 0:
            args += ["{}={}".format(k, v) for k, v in self.kwargs.items()]
        return '{}({})'.format(self.name, ', '.join(args))


class Pipeline(object):
    """ Pipeline.

    Pipelines are built by linking together a series
    of stages. Upon execution, the pipeline applies
    each stage to the given LimitlessLED group.
    """

    def __init__(self):
        """ Initialize pipeline.

        Stage methods are dynamically initialized
        since they all follow the same pattern.
        """
        self._pipe = []
        self._group = None
        stages = ['on', 'off', 'color', 'transition', 'flash', 'callback',
                  'repeat', 'brightness', 'wait', 'temperature', 'white',
                  'white_up', 'white_down', 'red_up', 'red_down',
                  'green_up', 'green_down', 'blue_up', 'blue_down',
                  'night_light']
        for name in stages:
            self._add_stage(name)

    @property
    def pipe(self):
        """ Pipe property. """
        return self._pipe

    @property
    def group(self):
        """ Group property. """
        return self._group

    @group.setter
    def group(self, group):
        """ Set the associated group.

        :param group: Associated group.
        """
        self._group = group

    def run(self, stop):
        """ Run the pipeline.

        :param stop: Stop event
        """
        _LOGGER.info("Starting a new pipeline on group %s", self._group)
        self._group.bridge.incr_active()
        for i, stage in enumerate(self._pipe):
            self._execute_stage(i, stage, stop)
        _LOGGER.info("Finished pipeline on group %s", self._group)
        self._group.bridge.decr_active()

    def append(self, pipeline):
        """ Append a pipeline to this pipeline.

        :param pipeline: Pipeline to append.
        :returns: This pipeline.
        """
        for stage in pipeline.pipe:
            self._pipe.append(stage)
        return self

    def _add_stage(self, name):
        """ Add stage methods at runtime.

        Stage methods all follow the same pattern.

        :param name: Stage name.
        """
        def stage_func(self, *args, **kwargs):
            """ Stage function.

            :param args: Positional arguments.
            :param kwargs: Keyword arguments.
            :return: Pipeline (for method chaining).
            """
            self._pipe.append(Stage(name, args, kwargs))
            return self

        setattr(Pipeline, name, stage_func)

    def _execute_stage(self, index, stage, stop):
        """ Execute a pipeline stage.

        :param index: Stage index.
        :param stage: Stage object.
        """
        if stop.is_set():
            _LOGGER.info("Stopped pipeline on group %s", self._group)
            return
        _LOGGER.info(" -> Running stage '%s' on group %s", stage, self._group)
        if stage.name == 'on':
            self._group.on = True
        elif stage.name == 'off':
            self._group.on = False
        elif stage.name == 'hue':
            self._group.hue = stage.args[0]
        elif stage.name == 'saturation':
            self._group.saturation = stage.args[0]
        elif stage.name == 'color':
            self._group.color = Color(*stage.args)
        elif stage.name == 'brightness':
            self._group.brightness = stage.args[0]
        elif stage.name == 'temperature':
            self._group.temperature = stage.args[0]
        elif stage.name == 'transition':
            self._group.transition(*stage.args, **stage.kwargs)
        elif stage.name == 'white':
            self._group.white()
        elif stage.name == 'white_up':
            self._group.white_up()
        elif stage.name == 'white_down':
            self._group.white_down()
        elif stage.name == 'red_up':
            self._group.red_up()
        elif stage.name == 'red_down':
            self._group.red_down()
        elif stage.name == 'green_up':
            self._group.green_up()
        elif stage.name == 'green_down':
            self._group.green_down()
        elif stage.name == 'blue_up':
            self._group.blue_up()
        elif stage.name == 'blue_down':
            self._group.blue_down()
        elif stage.name == 'night_light':
            self._group.night_light()
        elif stage.name == 'flash':
            self._group.flash(**stage.kwargs)
        elif stage.name == 'repeat':
            self._repeat(index, stage, stop)
        elif stage.name == 'wait':
            time.sleep(*stage.args)
        elif stage.name == 'callback':
            stage.args[0](*stage.args[1:], **stage.kwargs)

    def _repeat(self, index, stage, stop):
        """ Repeat a stage.

        :param index: Stage index.
        :param stage: Stage object to repeat.
        :param iterations: Number of iterations (default infinite).
        :param stages: Stages back to repeat (default 1).
        """
        times = None
        if 'iterations' in stage.kwargs:
            times = stage.kwargs['iterations'] - 1
        stages_back = 1
        if 'stages' in stage.kwargs:
            stages_back = stage.kwargs['stages']
        i = 0
        while i != times:
            if stop.is_set():
                break
            for forward in range(stages_back):
                if stop.is_set():
                    break
                stage_index = index - stages_back + forward
                self._execute_stage(stage_index, self._pipe[stage_index], stop)
            i += 1
