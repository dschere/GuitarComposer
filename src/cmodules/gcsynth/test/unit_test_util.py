import os
import gcsynth
import sys
import traceback

base_dir = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-5])


class timer_event:
    def __init__(self, when, channel, ev_type):
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

    def send(self):
        d = vars(self)
        gcsynth.timer_event(d)


class filter_add(timer_event):
    def __init__(self, when, channel, plugin_path, plugin_label):
        super().__init__(when, channel, gcsynth.EV_FILTER_ADD)
        self.plugin_path = plugin_path
        self.plugin_label = plugin_label


class filter_remove(timer_event):
    def __init__(self, when, channel, plugin_label):
        super().__init__(when, channel, gcsynth.EV_FILTER_REMOVE)
        self.plugin_label = plugin_label


class filter_enable(timer_event):
    def __init__(self, when, channel, plugin_label):
        super().__init__(when, channel, gcsynth.EV_FILTER_ENABLE)
        self.enable = 1


class filter_disable(timer_event):
    def __init__(self, when, channel, plugin_label):
        super().__init__(when, channel, gcsynth.EV_FILTER_DISABLE)
        self.enable = 0


class filter_control(timer_event):
    def __init__(self, when, channel, plugin_label, name, value):
        super().__init__(when, channel, gcsynth.EV_FILTER_CONTROL)
        self.control_name = name
        self.control_value = value


class noteon(timer_event):
    def __init__(self, when, channel, key, vel):
        print("before")
        print("gcsynth.EV_NOTEON = %d" % gcsynth.EV_NOTEON)
        super().__init__(when, channel, gcsynth.EV_NOTEON)
        self.midi_code = key
        self.velocity = vel


class noteoff(timer_event):
    def __init__(self, when, channel, plugin_label, key):
        super().__init__(when, channel, gcsynth.EV_NOTEOFF)
        self.midi_code = key


class pitch_change(timer_event):
    def __init__(self, when, channel, semitones):
        super().__init__(when, channel, gcsynth.EV_PITCH_WHEEL)
        self.pitch_change = semitones


def gcsynth_start_stop(func):
    def wrapper(*args, **kwargs):
        # Call gcsynth.start() before the function
        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"]
        }
        gcsynth.start(data)
        try:
            # Call the original function
            result = func(*args, **kwargs)
        except:
            traceback.print_stack()
        print("stopping synth")
        gcsynth.stop()
        return result
    return wrapper
