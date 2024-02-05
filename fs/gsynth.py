from fluidsynth import FluidSynthClient
import time
from midi import midiNoteNumber
from ctypes import CDLL
from sched import scheduler
from threading import Thread


MIDI_PITCH_CENTER = 8192
MIDI_PITCH_SENSITIVITY_IN_SEMITONES = 12


class USecDelay:
    "Functor that emulates sleep but using the C usleep"
    def __init__(self):
        self.standard_c_library = CDLL('libc.so.6')
        
    def __call__(self, n : float):
        usecs = int(n * 1000000)
        self.standard_c_library.usleep(usecs)



class SchedulerTask(Thread):
    def __init__(self, sched):
        super().__init__(daemon=True)
        self.sched = sched
        
    def getScheduler(self):
        return self.sched
    
    def run(self):
        # run in blocking mode
        self.sched.run(True)    
        

class HandEffects:
    """
    This class uses a scheduler thread that sets up midi events over time
    to emulate hand effects (slides, hammer on pull offs, vibrato) 
    """
    def __init__(self, fs_client: FluidSynthClient):
        v = MIDI_PITCH_CENTER / MIDI_PITCH_SENSITIVITY_IN_SEMITONES
        self.semitone_units = v
        self.fs_client = fs_client
            
    def linear_bend(self, 
                    chan: int,
                    duration: float, 
                    value: float):
        "bend in even increments "
        graph = []
        steps = 9
        for i in range(1, steps+1):
            v = (value * i)/steps
            graph.append(v)
        return self.pitch_changes(chan, duration, graph)  
    
    def fast_bend(self, 
                    chan: int,
                    duration: float, 
                    value: float):
        "bend in even increments "
        graph = [value] * 13
        steps = 7
        for i in range(0, steps):
            v = (value * i)/steps
            graph[i] = v
        return self.pitch_changes(chan, duration, graph)  
    
    
    def pitch_changes(self, 
             chan: int, 
             duration: float, 
             graph: []):
        """
        This is the base primitive for bends, slides and vibrato, what varies is
        the graph array which instructs pitches to be changed over time (x axis)
        and (pitch y axis). 
        
        x -> time units duration / len(graph)
        y -> bend units measured in semitones as float (0 mean no bend)
        
        Assumptions: 
            each channel has a sensitivity of 12 semitones so 
            0 means 12 semitones lower and 8192*2 means 12 semitones higher.
        """
        pitch = MIDI_PITCH_CENTER
        f = self.fs_client.pitch_bend
         

        # create a scheduler for pitch bend events on this channel
        s = scheduler(time.monotonic, USecDelay())
        
        for x in range(0, len(graph)):
            when = (duration * x) / len(graph)
            semitone = int(graph[x] * self.semitone_units)
            pitch = semitone + MIDI_PITCH_CENTER

            #print(f"{f} {when}  {chan} {pitch}")
            s.enter(when, 1, f, argument=(chan, pitch))
            
        task = SchedulerTask(s)
        task.start()    
            
        return task
        
        
        
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
        self.hand_effects = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None
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
        

def unittest():
    addr = '127.0.0.1'
    port = 2112
    fs_client = FluidSynthClient()
    fs_client.connect(port, addr)
    fs_client.start()
    fs_client.pitch_bend_range(0, 12) 

    time.sleep(1.0)

    fs_client.noteon(0, 60, 127)
    time.sleep(1.0)

    he = HandEffects(fs_client)
    s = he.linear_bend(0, 0.5, 4.0)
    time.sleep(10)
    
    
if __name__ == '__main__':
    unittest()    


