
from music.constants import Dynamic
from typing import List
from music.durationtypes import (WHOLE, 
        HALF, QUARTER, SIXTEENTH, THIRTYSECOND, SIXTYFORTH)
from models.effect import (Reverb,Distortion,ChorusFlanger,EffectModule) 
import logging
import math

class TimeSig:
    def __init__(self):
        # number of beat notes per measure 
        self.beats_per_measure = 4
        # code identifying what the beat is 4
        # is queater note, 8 is an eight note 
        self.beat_note_id = 4

    def beat_duration(self):
        return 4.0 / self.beat_note_id    

class TabEvent:
    BEND_PERIODS = 13

    REST = 0
    NOTE = 1
    CHORD = 2

    def classify(self):
        result = self.REST
        for val in self.fret:
            if val != -1:
                result += 1
                if result == self.CHORD:
                    break
        return result
    
    def __init__(self, num_gstrings):
        super().__init__()

        self.duration = QUARTER
        self.string = 5  # current string being edited
        self.fret = [-1] * num_gstrings  # current fret value
        self.tied_notes = [-1] * num_gstrings
        self.pitch_bend_histogram = [0] * self.BEND_PERIODS
        self.pitch_bend_active = False
        self.dotted = False
        self.double_dotted = False
        self.dynamic = Dynamic.MP
        self.triplet = False
        self.quintuplet = False
        self.legato = False
        self.staccato = False
        self.upstroke = False
        self.downstroke = False
        self.stroke_duration = SIXTEENTH
        self.effects : List[EffectModule] = []
        self.num_gstrings = num_gstrings

    def getEffects(self) -> List[EffectModule]:
        return self.effects

    def setEffects(self, el : List[EffectModule]):
        self.effects = el

    def update(self, other):
        for k,v in vars(other).items():
            setattr(self,k,v) 

    def beats(self, beat_note_dur: float):
        # If 6/8 time, then beat_note_dur is 0.5 so 
        # a quater note (duration=1.0) is actually 2 beats.
        beats = self.duration / beat_note_dur
        if self.duration != WHOLE:
            if self.dotted:
                beats *= 1.5
            if self.double_dotted:
                beats *= 1.75
            if self.triplet:
                beats *= 0.66666
            if self.quintuplet:
                beats *= 0.2
        return beats





class Measure:
    def __init__(self, **kwargs):
        # a list of tab events in the order they are in the staff

        # If either of these are None then the prior measure timespec / cleff
        # are used. The first measure always contains one.
        self.timesig :TimeSig | None = kwargs.get('timesig')
        #self.cleff : str | None = kwargs.get('cleff')
        self.bpm = kwargs.get('bpm')
        self.key = kwargs.get('key')
        # I don't think we would every change the cleff on a track
        self.staff_changes = self.timesig or self.bpm or self.key

        self.tab_events : List[TabEvent] = []
        self.current_tab_event = 0

        self.start_repeat = kwargs.get('start_repeat',False)
        self.end_repeat = kwargs.get('end_repeat',False)
        self.repeat_count = kwargs.get('repeat_count',-1)
        self.measure_number = kwargs.get('measure_number',1)
        self.beat_error_msg = ""
        
    def insert_after_current(self, tab_event : TabEvent):
        i = self.current_tab_event
        self.insert(tab_event, i)

    def insert(self, tab_event : TabEvent, i : int):
        if i >= 0 and i < len(self.tab_events):
            n = self.tab_events[:i] + [tab_event] + self.tab_events[i:]
            self.tab_events = n

    def remove_current(self):
        del self.tab_events[self.current_tab_event]
        self.current_tab_event = self.current_tab_event % len(self.tab_events)        

    def append(self, tab_event : TabEvent):
        self.tab_events.append(tab_event)        

    def delete(self, i : int):
        if i >= 0 and i < len(self.tab_events):
            del self.tab_events[i]

    def set_timespec(self, timespec : TimeSig):
        self.timesig = timespec

    def set_cleff(self, cleff : str):
        self.cleff = cleff

    def update_beat_errmsg(self, ts: TimeSig):
        beats = 0.0
        for e in self.tab_events:
            beats += e.beats(ts.beat_duration())

        # beats rounded to the nearest 1/100
        # In the case of a triplet then I have to handle the case 
        # of beats being a repeating decimal like 3.999 ...
        beats = math.ceil(beats * 100) / 100
        
        logging.debug(f"beats = {beats}")
        if ts.beats_per_measure == beats:
            self.beat_error_msg = ""
        elif beats > ts.beats_per_measure:
            self.beat_error_msg = "Too many beats in measure"
        elif beats < ts.beats_per_measure:
            self.beat_error_msg = "Too few beats in measure" 

    def exceeds_beat_threshold(self, ts: TimeSig, te: TabEvent|None = None):
        """
        Compute whether or not the total duration of all tab events exceeds
        the allowed number of beats allowed in this measure. 

        If 'te' is defined then it will be added to the sum, allowing this function 
        to act as a validation function.
        """
        beats = 0.0
        
        if te:
            beats = te.beats(ts.beat_duration())
        for e in self.tab_events:
            beats += e.beats(ts.beat_duration())
            if beats > ts.beats_per_measure:
                return True
        # pass checks    
        return False

