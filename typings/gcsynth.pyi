from typing import Any

EV_FILTER_ADD: int
EV_FILTER_CONTROL: int
EV_FILTER_DISABLE: int
EV_FILTER_ENABLE: int
EV_FILTER_REMOVE: int
EV_NOTEOFF: int
EV_NOTEON: int
EV_PITCH_WHEEL: int
NUM_CHANNELS: int

class GcsynthException(Exception): ...

def channel_gain(chan, v) -> Any: ...
def filter_add(*args, **kwargs): ...
def filter_disable(*args, **kwargs): ...
def filter_enable(*args, **kwargs): ...
def filter_query(*args, **kwargs): ...
def filter_remove(*args, **kwargs): ...
def filter_set_control_by_index(*args, **kwargs): ...
def filter_set_control_by_name(chan, plugin_label, name, value) -> Any: ...
def noteoff(chan, midicode) -> Any: ...
def noteon(chan, midicod, velocity) -> Any: ...
def reset_channel(chan) -> Any: ...
def select(chan, sfont_id, bank, preset) -> Any: ...
def start(*args, **kwargs): ...
def stop(*args, **kwargs): ...
def test_filter(path: str, plugin_label: str): ...
def timer_event(*args, **kwargs): ...
def pitchrange(chan: int, semitones: float): ...
def pitchwheel(chan: int, semitones: float): ...
def ladspa_plugin_labels(filepath: str): ...