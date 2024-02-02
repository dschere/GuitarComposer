"""
Represents a single track in a music composition.


Array of measures.
   meter (default 4/4)
   key (default C major)
   temp (default 120)

   event
       rest
       note/chord
       
"""


        


class Event:
    def __init__(self, tick):
        self.tick = tick
        

class KeyChangeEvent(Event):
    def __init__(self, tick, key):
        super().__init__(tick)
        self.key = key
    
class TempoChangeEvent(Event):
    def __init__(self, tick, tempo):
        super().__init__(tick)
        self.tempo = tempo
            
class MeteChangeEvent(Event):
    def __init__(self, tick, meter):
        super().__init__(tick)
        self.meter = meter
        
class NoteEvent(Event):
    def __init__(self, tick, **kwargs):
        super().__init__(tick)
        # duration in beats 
        self.duration = kwargs.get('duration', 1)
        # pitch expressed as a midi note code
        self.pitch = kwargs.get('pitch', 1)
        


class Measure:
    def __init__(self):
        self.key = "C"
        self.tempo = 120
        self.meter = [4,4]
        self.events = []


class Tuning:
    def __init__(self):
        self.string = []

class TrackModel:
    def __init__(self, **kwargs):
        self.measures = []
        self.tuning = kwargs.get('tuning', StandardTuning)
