# python-limitlessled

`python-limitlessled` controls LimitlessLED bridges. It supports `white` and `rgbw` bulb groups.

## Usage
### Configure
Your bridge(s) must be set up and bulbs joined prior to using this module.

Group names can be any string, but must be unique amongst all bridges.
```python
from limitlessled.bridge import Bridge
from limitlessled.group.rgbw import RGBW
from limitlessled.group.white import WHITE

bridge = Bridge('<your bridge ip address>')
bridge.add_group(1, 'bedroom', RGBW)
# A group number can support two groups as long as the types differ
bridge.add_group(2, 'bathroom', WHITE)
bridge.add_group(2, 'living_room', RGBW)
```

Get access to groups either via the return value of `add_group`, or with the `LimitlessLED` object.

```python
bedroom = bridge.add_group(1, 'bedroom', RGBW)
# or
limitlessled = LimitlessLED()
limitlessled.add_bridge(bridge)
bedroom = limitlessled.group('bedroom')
```

### Control

Turn on:
```python
bedroom.on = True
```

Change brightness:
```python
bedroom.brightness = 0.5 # 0.0 through 1.0
```

Change temperature (white groups only)
```python
bedroom.temperature = 0.5 # 0.0 through 1.0
```

Change color (rgbw groups only)

LimitlessLED RGBW bulbs can represent only the hue component of RGB color. There are 256 possible values, starting with blue as 0. Maximum saturation and value are always used. This means that most RGB colors are not supported. There are two special cases: Black (0, 0, 0) is simply all LEDs turned off. White (255, 255, 255) is the RGB LEDs off and the white LED on. Note that the actual color of the white LED depends on whether the bulb is a cool white or a warm white bulb.

```python
from limitlessled import Color
bedroom.color = Color(255, 0, 0) # red
```

Transition
```python
bedroom.transition(brightness=1.0, temperature=0.1) # white groups

from limitlessled import Color
bedroom.transition(brightness=1.0, color=Color(0, 255, 0)) # rgbw groups
```

#### Pipelines

Pipelines specify a sequence of stages, each stage being a command. Pipelines are not executed until called as an argument to a group's `enqueue` method.

Pipelines are executed in a thread (per group). Multiple pipelines can be started on a group; they will queue and execute in the order received.

A bridge can run multiple pipelines concurrently provided they are on different groups. Note that concurrency is achieved by interleaving commands, and as a consequence, pipeline execution can take longer than specified and each pipeline may use fewer transition steps depending on the number of concurrently executing pipelines.

```python
from limitlessled import Color
from limitlessled.pipeline import Pipeline

pipeline = Pipeline() \
    .on() \
    .brightness(0.7) \
    .color(0, 0, 255) \
    .transition(color=Color(255, 0, 0))
    
bedroom.enqueue(pipeline)
```

Stop the currently-running pipeline:
```python
bedroom.stop()
```

##### Commands

Turn on
```python
Pipeline().on()
```

Turn off
```python
Pipeline().off()
```

Set brightness
```python
Pipeline().brightness(0.5)
```

Set temperature
```python
Pipeline().temperature(0.5)
```

Set color
```python
Pipeline().color(255, 0, 0)
```

Transition
```python
Pipeline.transition(...)
```

Wait
```python
Pipeline.wait(4) # in seconds
```

Repeat

`stages` is how many previous stages to repeat
`iterations` is how many times to repeat stages

Default `stages` is `1`, default `iterations` is infinite.
```python
Pipeline().repeat(stages=2, iterations=3)
```
Callback
```python
def my_function():
    pass

Pipeline().callback(my_function)
```

Append
```python
p1 = Pipeline.off()

p2 = Pipeline.on().append(p1)
```

## Contributions

Pull requests welcome. Some areas for enhancement include

- Discovery
- Pairing
