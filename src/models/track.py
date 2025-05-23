# import logging
# from music.constants import Dynamic
# from typing import List, Optional
# from music.durationtypes import (WHOLE, 
#         HALF, QUARTER, SIXTEENTH, THIRTYSECOND, SIXTYFORTH)
# from collections import OrderedDict
# import copy
# from singleton_decorator.decorator import singleton
# from bisect import bisect_left
# import json

from models.measure import Measure, TimeSig, TabEvent 
from typing import List, Optional, Tuple
from models.effect import Effects
from services.effectRepo import EffectRepository

class Track:
    FIRST_NOTE_COLUMN = 2

    def blank_measure(self, **kwargs):
        """
        Setup a new blank track with a default Staff and measure. 
        """
        measure = Measure(**kwargs)
        if "timesig" in kwargs:
            ts = kwargs["timesig"]
        else:
            ts = self.get_timesig() 

        for _ in range(ts.beats_per_measure):
            tab_event = TabEvent(len(self.tuning))
            measure.append(tab_event)
        return measure
    
    def getMeasureParams(self, m : Measure) -> Tuple[TimeSig, int, str, str]:
        ts = self.measures[0].timesig
        bpm = self.measures[0].bpm
        key = self.measures[0].key
        cleff = self.cleff 
        for measure in self.measures[1:]:
            if measure is m:
                break
            if measure.timesig:
                ts = measure.timesig 
            if measure.bpm:
                bpm = measure.bpm
            if measure.key:
                key = measure.key
        assert(ts)
        assert(bpm)
        assert(key)        
        return (ts, bpm, key, cleff)

    def __init__(self, cleff = None):
        self.instrument_name = "Acoustic Guitar"
        # instrument currently allocated for this track.
        self.tuning = [
            "E4",
            "B3",
            "G3",
            "D3",
            "A2",
            "E2"
        ]
        self.current_measure = 0

        # create a default Measure as a starter
        # 4/4 time, bpm 120 and in the key of C
        from view.editor.glyphs.common import TREBLE_CLEFF

        if not cleff:
            self.cleff = TREBLE_CLEFF
        else:
            self.cleff = cleff
        m = self.blank_measure(
            timesig=TimeSig(), 
            bpm=120, 
            key="C")
        m.cleff = self.cleff
        self.measures : List[Measure] = [m]

        # effects to be applied to this track
        self.effects = EffectRepository().create_effects()


    def append_measure(self, **kwargs):
        m = self.blank_measure(**kwargs)
        self.measures.append(m)   
        m.cleff = self.cleff
        return m 
        

    def get_timesig(self) -> TimeSig:
        """
        get the timesig relative to current measure
        
        There can be multiple time signatures in a track, starting
        with the current measure walk back towards the start to
        find the current time signature. The first measure always
        has a time signature.
        """
        for i in range(self.current_measure,-1,-1):
            if self.measures[i].timesig:
                return self.measures[i].timesig # type: ignore
            
        raise RuntimeError("At least the first measure should have a timesig")

    def remove_measure(self):
        if len(self.measures) > 0:
            del self.measures[self.current_measure]
            if self.current_measure >= len(self.measures):
                self.current_measure = len(self.measures) - 1
            for (mn, m) in enumerate(self.measures):
                m.measure_number = mn + 1        
            
    def current_moment(self) -> Tuple[TabEvent, Measure]:
        m = self.measures[self.current_measure] 
        return (m.tab_events[m.current_tab_event], m)

    def get_measure(self, from_current=0):
        i = self.current_measure + from_current 
        if i >= 0 and i < len(self.measures):
            return self.measures[i]    

    def find_tab_measure(self, tab_event: TabEvent) -> Measure | None:
        for m in self.measures:
            if tab_event in m.tab_events:
                return m
    
    def get_effects(self, te: TabEvent) -> Effects | None:
        """
        track         ----             ---- te
           <default>      effect change      +-> we want this effect settings
                               +-------------------------/\
        """
        # get the default effect settings for this track
        e = self.effects 
        for m in self.measures:
            for t in m.tab_events:
                if t is te:
                    break
                # the composer could have changed the default effect
                elif t.effects:
                    e = t.effects
        return e
    
    def skip_measure(self):
        "skip the current measure to next one"
        if (self.current_measure+1) < len(self.measures):
            self.current_measure += 1
            m = self.measures[self.current_measure]
            m.current_tab_event = 0

    def previous_measure(self):
        if self.current_measure > 0:
            self.current_measure -= 1
            m = self.measures[self.current_measure]
            m.current_tab_event = 0

    def next_moment(self) -> Tuple[Optional[TabEvent], Measure]:
        """
        Increments the current tab event in the current measure.
        If no more tab events returns None. 
        """
        m = self.measures[self.current_measure]
        tab_event = None 

        if (m.current_tab_event+1) < len(m.tab_events):
            # we are not at the end of the return the next tab
            m.current_tab_event += 1
            tab_event = m.tab_events[m.current_tab_event]     
        
        elif (self.current_measure+1) < len(self.measures):
            # we are are still measures, increment current measure
            # and go to the first tab event
            self.current_measure += 1
            m = self.measures[self.current_measure]
            m.current_tab_event = 0
            tab_event = m.tab_events[0]
        
        # at the last tab of the last measure return None
        return (tab_event,m)

    def prev_moment(self) -> Tuple[Optional[TabEvent], Measure]:
        m = self.measures[self.current_measure]
        tab_event = None

        if m.current_tab_event > 0:
            # not at the beginning of the measure decrement 
            # current tab event and return assicate tab event
            m.current_tab_event -= 1
            tab_event = m.tab_events[m.current_tab_event]

        elif self.current_measure > 0:
            # there are still measures before this one to 
            # go back to.
            self.current_measure -= 1
            m = self.measures[self.current_measure]
            m.current_tab_event = len(m.tab_events) - 1
            tab_event = m.tab_events[m.current_tab_event]

        # at the first tab of the first measure return None
        return (tab_event,m)

    def set_moment(self, measure: int, tab: int):
        if measure < len(self.measures):
            self.current_measure = measure
            m = self.measures[self.current_measure]
            if tab < len(m.tab_events):
                m.current_tab_event = tab
        
    def is_last_moment(self):
        if self.current_measure == (len(self.measures)-1):
            m = self.measures[self.current_measure] 
            if m.current_tab_event == (len(m.tab_events)-1):
                return True
        return False

    def createTabEvent(self, inherit=None) -> TabEvent:
        te = TabEvent(len(self.tuning))
        if inherit:
            te.duration = inherit.duration
            te.dynamic = inherit.dynamic
            te.legato = inherit.legato
            te.staccato = inherit.stacatto
            te.triplet = inherit.triplet
            te.quintuplet = inherit.quintuplet
        return te

    def computeMidiCodes(self, te: TabEvent):
        raise FutureWarning("TODO: compute midi code based on tuning")

    def setTuning(self, tuning):
        self.tuning = tuning

