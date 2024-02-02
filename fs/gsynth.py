from fluidsynth import FluidSynthClient
import time
from threading import Thread, Event
from midi import midiNoteNumber

class HandEffect(Thread):
    def __init__(self, event_list=[]):
        super().__init__(daemon=True)
        self.running = Event()
        # list of [(delay, func, args), ... ]
        self.event_list = event_list
        
    def stop(self):
        self.running.clear()    
        
    def run(self):
        self.running.set()
        
        for (delay, func, args) in self.event_list:
            if not self.running.is_set():
                break
            time.sleep(delay)
            func(*args)
            
        self.running.clear()

        
class GSynth(FluidSynthClient):
    def __init__(self):
        super().__init__()

        self.tuning = {
            1: midiNoteNumber("E2"),
            2: midiNoteNumber("A2"),
            3: midiNoteNumber("D3"),
            4: midiNoteNumber("G3"),
            5: midiNoteNumber("B3"),
            6: midiNoteNumber("E4")            
        }
        self.state = {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False
        }   
        
    def set_tuning(self, gstr, midiName):
        self.tuning[gstr] = midiNoteNumber(midiName)   
        
    def _setup(self):
        # Special sound font where each instrument code
        # corresponds to a guitar string.
        for i in range(0, 6):
            self.prog(i, i)
            self.pitch_bend_range(i, 12)
            
    def run(self):
        # set settings in the synthesize.
        # each guitar string is assigned a separate channel
        # and treated as a separate instrument.
        self._setup()

