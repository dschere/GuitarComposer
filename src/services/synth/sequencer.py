"""
Allows for events for all tracks to be condensed
to a single linears sequence of events. Some events
such as bends/slides translate to multiple events
over time.
"""
import typing
import gcsynth


class timer_event:
    def __init__(self, when: int, channel: int, ev_type: int):
        self.when = when
        self.channel = channel
        self.ev_type = ev_type
        self.midi_code = 40
        self.velocity = 64
        self.plugin_label = ""
        self.plugin_path = ""
        self.enable = 0
        self.control_name = ""
        self.control_value = 0.0
        self.pitch_change = 0.0

    def encode(self) -> dict:
        return vars(self)
    


class noteon(timer_event):
    def __init__(self, when, channel, key, vel):
        super().__init__(when, channel, gcsynth.EV_NOTEON)
        self.midi_code = key
        self.velocity = vel

class noteoff(timer_event):
    def __init__(self, when, channel, key):
        super().__init__(when, channel, gcsynth.EV_NOTEOFF)
        self.midi_code = key


class pitch_change(timer_event):
    """
    changes the pitch in semitones.

    value: 0.0 means no change, range -12.0 to 12.0 
    """

    def __init__(self, when: int, channel: int, value: float):
        super().__init__(when, channel, gcsynth.EV_PITCH_WHEEL)
        self.pitch_change = value


class filter_add(timer_event):
    def __init__(self, when: int, channel: int, plugin_path: str, plugin_label: str):
        super().__init__(when, channel, gcsynth.EV_FILTER_ADD)
        self.plugin_path = plugin_path
        self.plugin_label = plugin_label


class filter_remove(timer_event):
    def __init__(self, when: int, channel: int, plugin_label: str):
        super().__init__(when, channel, gcsynth.EV_FILTER_REMOVE)
        self.plugin_label = plugin_label


class filter_enable(timer_event):
    def __init__(self, when: int, channel: int, plugin_label: str):
        super().__init__(when, channel, gcsynth.EV_FILTER_ENABLE)
        self.enable = 1
        self.plugin_label = plugin_label


class filter_disable(timer_event):
    def __init__(self, when: int, channel: int, plugin_label: str):
        super().__init__(when, channel, gcsynth.EV_FILTER_DISABLE)
        self.enable = 0
        self.plugin_label = plugin_label


class filter_control(timer_event):
    def __init__(self, when: int, channel: int, plugin_label: str, name: str, value: float):
        super().__init__(when, channel, gcsynth.EV_FILTER_CONTROL)
        self.control_name = name
        self.control_value = value


class sequencer:
    def __init__(self, synth_service):
        # when (millisecs) -> [timer_event, ...]
        self.te_events = {}
        self.synth_service = synth_service

    def add(self, te: timer_event):
        items = self.te_events.get(te.when, [])
        items.append(te)
        self.te_events[te.when] = items

    def play(self):
        # flatten dictionary sorted by timer event
        play_list = []
        for (when, te_list) in sorted(self.te_events):
            play_list += te_list
        self.synth_service.timer_event(play_list)
