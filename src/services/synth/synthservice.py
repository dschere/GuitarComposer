import gcsynth 

from singleton_decorator import singleton
from services.synth.instrument_info import instrument_info
from services.synth.sequencer import sequencer
import atexit
import signal

class midi_channel_manager:
    DRUM_CHANNEL = 9

    def __init__(self, synth):
        self.c_index = 1
        self.synth = synth
        self.num_channels = gcsynth.LIVE_CAPTURE_CHANNEL-1
        self.channel_state = [None for i in range(self.num_channels)]

    def checkout_channel(self):
        chan = None
        for i in range(self.num_channels):
            if not self.channel_state[self.c_index]:
                chan = self.c_index

            # ring increment counter, skip over the drum channel
            self.c_index = (self.c_index + 1) % self.num_channels
            if self.c_index == self.DRUM_CHANNEL:
                self.c_index += 1

            if chan:
                break
        return chan

    def reset(self):
        self.c_index = 1

    def dealloc(self, chan):
        self.synth.reset_channel(chan)
        self.channel_state[chan] = None

    def alloc(self, instrument_name):
        spec = self.synth.find(instrument_name)
        if not spec:
            raise ValueError("Unknown instrument name '%s'" %
                             instrument_name)
        chan = self.checkout_channel()
        if not chan:
            raise RuntimeError("Not enough channels!")

        self.channel_state[chan] = spec
        self.synth.select(
            chan,
            spec.sfont_id,
            spec.bank_num,
            spec.preset_num
        )
        return chan



@singleton
class synthservice:
    """
    A thin wrapper around the gcsynth cmodule.

    The underlying fluidsynth thread is launched in app.py before
    the Qt Application is created.
    """
    def __init__(self):
        # scan soundfonts and produce an archive of information
        # filenames, instrument data etc.
        self.db = instrument_info()
        self.cm = midi_channel_manager(self)
        
        # stop audio threads on exit
        atexit.register(self.shutdown)

    def reset_channel_manager(self):
        self.cm.reset()

    def dealloc(self, chan):
        self.cm.dealloc(chan)

    def alloc(self, instrument_name):
        return self.cm.alloc(instrument_name)

    def find(self, instrument_name):
        """lookup instrument information that can be used to setup a channel"""
        return self.db.find(instrument_name)

    def shutdown(self):
        # perform cleanup here is anything needs to be done.

        # stop synth thread
        self.stop()
        # failsafe in case there some race condition during shutdown
        signal.alarm(2)


    def getSequencer(self):
        return sequencer(self)

    def reset_channel(self, chan):
        return gcsynth.reset_channel(chan)

    def start(self):
        return gcsynth.start({"sfpaths": self.db.sfpaths})
    
    def list_capture_devices(self):
        return gcsynth.list_capture_devices()
    
    def start_capture(self, device: str):
        return gcsynth.start_capture(device)
    
    def stop_capture(self):
        return gcsynth.stop_capture()

    def get_live_channel(self):
        return gcsynth.LIVE_CAPTURE_CHANNEL

    def stop(self):
        return gcsynth.stop()

    def noteoff(self, channel: int, midicode: int, gstring= -1):
        return gcsynth.noteoff(channel, midicode, gstring)

    def noteon(self, channel: int, midicode: int, velocity: int, gstring =-1):
        #print(f"gcsynth.noteon(channel={channel}, midicode={midicode}, velocity={velocity})")
        return gcsynth.noteon(channel, midicode, velocity, gstring)

    def select(self,
               channel: int,
               sfont_id: int,
               bank_num: int,
               preset_num: int):
        return gcsynth.select(channel, sfont_id, bank_num, preset_num)

    def filter_add(self, channel: int,
                   filepath: str, plugin_label: str):
        return gcsynth.filter_add(channel, filepath, plugin_label)

    def filter_remove(self, channel: int, plugin_label: str):
        return gcsynth.filter_remove( channel, plugin_label)

    def filter_remove_all(self, channel: int):
        return gcsynth.filter_remove(channel)

    def filter_query(self, filepath: str, plugin_label: str):
        return gcsynth.filter_query(filepath, plugin_label)

    def filter_enable(self, channel: int, plugin_label: str):
        return gcsynth.filter_enable(channel, plugin_label)

    def filter_disable(self, channel: int, plugin_label: str):
        return gcsynth.filter_disable( channel, plugin_label)

    def filter_set_control_by_name(self, channel: int,
                                   plugin_label: str,
                                   name: str, value: float):
        return gcsynth.filter_set_control_by_name(
                channel, plugin_label, name, value)

    def filter_set_control_by_index(self,
                                    channel: int, plugin_label: str,
                                    index: int, value: float):
        return gcsynth.filter_set_control_by_index(
                             channel, plugin_label, index, value)

    def channel_gain(self, channel: int, change: float):
        return gcsynth.channel_gain( channel, change)

    def timer_event(self, ev_or_ev_list):
        print(f"timer event called {ev_or_ev_list}")
        return gcsynth.timer_event( ev_or_ev_list)
    
    def pitch_range(self, channel: int, semitones: float):
        return gcsynth.pitchrange(channel, semitones)

    def pitch_change(self, channel: int, semitones: float):
        return gcsynth.pitchwheel(channel, semitones)

    def instrument_info(self):
        return self.db.instruments




if __name__ == '__main__':
    import time

    ss = synthservice()
    ss.start()
    ss.noteon(0, 60, 80)
    time.sleep(2.0)
    ss.stop()
    ss.shutdown()
