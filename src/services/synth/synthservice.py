from singleton_decorator import singleton
from services.synth.instrument_info import instrument_info

import gcsynth
from services.synth.sequencer import sequencer


@singleton
class synthservice:
    def __init__(self):
        # scan soundfonts and produce an archive of information
        # filenames, instrument data etc.
        self.db = instrument_info()

    def getSequencer(self):
        return sequencer(self)        

    def start(self):
        gcsynth.start({"sfpaths": self.db.sfpaths})

    def stop(self):
        gcsynth.stop()

    def noteoff(self, channel : int, midicode: int):
        gcsynth.noteoff(self, channel, midicode)

    def noteon(self, channel : int , midicode: int, velocity: int):    
        gcsynth.noteon(channel, midicode, velocity)

    def select(self, channel : int , sfont_id : int, bank_num : int , preset_num : int):
        gcsynth.select(channel, sfont_id, bank_num, preset_num)

    def filter_add(self, channel: int, filepath: str, plugin_label: str):
        gcsynth.filter_add(channel, filepath, plugin_label)

    def filter_remove(self, channel: int, plugin_label: str):
        gcsynth.filter_remove(channel, plugin_label)

    def filter_remove_all(self, channel: int):
        gcsynth.filter_remove(channel)

    def filter_query(self, filepath: str, plugin_label: str):
        return gcsynth.filter_query(filepath, plugin_label)
    
    def filter_enable(self, channel: int, plugin_label: str):
        gcsynth.filter_enable(channel, plugin_label)

    def filter_disable(self, channel: int, plugin_label: str):
        gcsynth.filter_disable(channel, plugin_label)

    def filter_set_control_by_name(self, channel: int, plugin_label: str, name: str, value: float):
        gcsynth.filter_set_control_by_name(channel, plugin_label, name, value)

    def filter_set_control_by_index(self, channel: int, plugin_label: str, index: int, value: float):
        gcsynth.filter_set_control_by_index(channel, plugin_label, index, value)

    def channel_gain(self, channel: int, change: float):
        gcsynth.channel_gain(channel, change)

    def timer_event(self, ev_or_ev_list):
        gcsynth.timer_event(ev_or_ev_list)

    def instrument_info(self):
        return self.db.instruments
    
    

