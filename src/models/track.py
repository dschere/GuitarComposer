import logging
from music.constants import Dynamic
from typing import List, Optional
from music.durationtypes import (WHOLE, 
        HALF, QUARTER, SIXTEENTH, THIRTYSECOND, SIXTYFORTH)
from collections import OrderedDict
import copy
from singleton_decorator.decorator import singleton
from bisect import bisect_left
import json

class TrackEvent:
    def pretty_print(self):
        v = vars(self)
        t = json.dumps(v, skipkeys=True, sort_keys=True, indent=4)
        print(self.__class__.__name__ + " " + t) 

    def __init__(self):
        pass

class StaffTimeSpec:
    def __init__(self):
        self.beats_per_measure = 0
        self.beat_duration = 1.0

class StaffEvent(TrackEvent):
    def __init__(self):
        TrackEvent.__init__(self)
        self.bpm = 120
        self.signature = "4/4"
        self.key = "C"

        # workaround for a circular import error.
        from view.editor.glyphs.common import TREBLE_CLEFF

        self.cleff = TREBLE_CLEFF

    def compute_timespec(self) -> StaffTimeSpec:
        s = StaffTimeSpec()
        ts = self.signature.split("/")
        s.beats_per_measure = int(ts[0])
        # note type that represents a beat, translated to a duration
        # 4 = quater note
        s.beat_duration = 4.0/int(ts[1])
        return s
        


class MeasureEvent(TrackEvent):
    def __init__(self):
        TrackEvent.__init__(self)
        self.start_repeat = False
        self.end_repeat = False
        self.repeat_count = 1
        self.measure_number = 1


class ChordEvent(TrackEvent):
    UPSTROKE = 0
    DOWNSTROKE = 1
    NOSTROKE = -1

    def __init__(self):
        super().__init__()
        self.stroke = self.DOWNSTROKE
        self.stroke_duration = 0  # in beats
        self.note_events = []


class EffectPresetEvent(TrackEvent):
    def __init__(self):
        super().__init__()


class AudioClipEvent(TrackEvent):
    def __init__(self):
        super().__init__()

        # play start and end
        self.start_pos = 0
        self.end_pos = 0
        self.loop = False
        self.filename = ""

# (computed_duration,doted,double_dotted,triplet,quintuplet,base_duration)
@singleton
class _duration_table:
    _lookup = []
    for _dur in (WHOLE, 
        HALF, QUARTER, SIXTEENTH, THIRTYSECOND, SIXTYFORTH):
        _lookup.append((_dur, False, False, False, False,_dur))
        if _dur == WHOLE:
            continue
        _lookup.append((_dur*1.5, True, False, False, False,_dur))
        _lookup.append((_dur*1.75, False, True, False, False,_dur))
        _lookup.append((_dur*0.666, False, False, True, False,_dur))
        _lookup.append((_dur*0.2, False, False, False, True,_dur))
    # sort ascending
    _lookup = sorted(_lookup, key=lambda item: item[0])
    _durList = [item[0] for item in _lookup]
  
    def nearest(self, t):
        #?? By doing a binary seach if this fails often its actually a performance
        # hit. Not sure, need testing to make sure its desirable.
        i = bisect_left(self._durList, t) 
        # did we find an exact match ?
        if i != len(self._durList) and self._durList[i] == t:
            return self._lookup[i]
        else:
            # no we will find a best match
            for (i,dur) in enumerate(self._durList):
                if t < dur:
                    if i > 0:
                        return self._lookup[i-1]
                    return self._lookup[i]

DurationTable = _duration_table()


class TabEvent(TrackEvent):
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
    
    def clone_from_beats(self, beat: float, beat_note_dur: float):
        t = beat * beat_note_dur
        r : TabEvent = copy.deepcopy(self)
        (_, r.dotted, 
         r.double_dotted, 
         r.triplet, 
         r.quintuplet, 
         r.duration) = DurationTable.nearest(t)
        r.note_duration = t
        return r
    
    def clone(self):
        r = copy.deepcopy(self)
        r.fret = [-1] * self.num_gstrings  # current fret value
        r.tied_notes = [-1] * self.num_gstrings
        r.pitch_bend_histogram = [0] * self.BEND_PERIODS
        r.pitch_bend_active = False
        return r


    def __init__(self, num_gstrings):
        super().__init__()

        self.duration = QUARTER
        self.string = 5  # current string being edited
        self.fret = [-1] * num_gstrings  # current fret value
        self.tied_notes = [-1] * num_gstrings
        self.note_duration = QUARTER
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

        self.num_gstrings = num_gstrings

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
                beats *= 0.66
            if self.quintuplet:
                beats *= 0.2
        return beats



class TrackEventSequence:
    """ 
    Events are generated by the UI, they result in this sequence being generated.

    This sequence is saved and used to generate a score.
    """
    STAFF_EVENT = 0
    MEASURE_EVENT = 1
    EFFECT_EVENT = 2
    AUDIO_EVENT = 3
    TAB_EVENT = 4

    _lookup = {
        STAFF_EVENT: StaffEvent,
        MEASURE_EVENT: MeasureEvent,
        EFFECT_EVENT: EffectPresetEvent,
        AUDIO_EVENT: AudioClipEvent,
        TAB_EVENT: TabEvent
    }

    FORWARD = 1
    BACKWARD = -1

    def pretty_print(self):
        print("track sequence:")
        for moment, evtList in self.data.items():
            print(f"moment = {moment}")
            for evt in evtList:
                evt.pretty_print()

    def __init__(self):
        # moment -> list of events
        self.data = OrderedDict()

    def getData(self) -> OrderedDict:
        return self.data

    def isEmpty(self):
        return len(self.data) == 0    

    def search(self, moment: int, direction: int, event_type: int):
        "search event list for a specific event type, return (moment,evt)"
        assert (event_type in self._lookup)
        assert (direction in (self.FORWARD, self.BACKWARD))
        
        klass = self._lookup[event_type]
            
        if direction == self.BACKWARD:
            m = moment
            while m > -1:
                for evt in self.data[m]:
                    if isinstance(evt, klass):
                        return (m, evt)
                m -= 1
        else:
            m = moment
            while m < len(self.data):
                for evt in self.data[m]:
                    if isinstance(evt, klass):
                        return (m, evt)
                m += 1

        """
        if moment in self.data:
            klass = self._lookup[event_type]
            keys = list(self.data.keys())
            if direction == self.FORWARD:
                mlist = keys[moment:]
            else:
                mlist = keys[:moment+1]
                mlist.reverse()
            for m in mlist:
                for evt in self.data[m]:
                    if isinstance(evt, klass):
                        return (m, evt)
        """
                        
        raise ValueError(f"unable to find {event_type} in sequence")

    def getActiveStaff(self, moment) -> StaffEvent | None:
        (_, evt) = self.search(moment, self.BACKWARD, self.STAFF_EVENT)
        return evt

    def add(self, moment: int, evt: TrackEvent):
        """
        add a new track event to a list of events for a given moment. 
        """
        evtList = self.data.get(moment, [])
        evtList.append(evt)
        self.data[moment] = evtList
        # self.momentList.sort()

       

    def get(self, moment: int) -> Optional[List[TrackEvent]]:
        return self.data.get(moment)

    def getEvent(self, moment: int, ev_type: int):
        klass = self._lookup[ev_type]
        for evt in self.data.get(moment,[]):
            if isinstance(evt, klass):
                return evt

    def apply(self, start: int, func):
        moment = start
        while moment < len(self.data):
            evtList = self.data[moment]
            func(moment, evtList)
            moment += 1
            
    def getBeats(self, moment: int, beat_note_dur: float):
        beats = 0
        te = self.getEvent(moment, self.TAB_EVENT)
        if te:
            beats = te.beats(beat_note_dur) 
        return beats

    def remove(self, moment: int, evt=None):
        if evt:
            evtList = self.data.get(moment)
            if evtList and evt in evtList:
                i = evtList.index(evt)
                del evtList[i]
                if len(evtList) == 0:
                    del self.data[moment]
        elif moment in self.data:
            del self.data[moment]

    def lastTabEventMoment(self):
        (moment,_) = self.search(len(self.data)-1,self.BACKWARD,self.TAB_EVENT)
        return moment

class Track:
    FIRST_NOTE_COLUMN = 2

    def __init__(self):
        self.uuid = None
        self.instrument_name = "Acoustic Guitar"
        self.tuning = [
            "E4",
            "B3",
            "G3",
            "D3",
            "A2",
            "E2"
        ]
        # beats from start of track -> [events]
        self.sequence = TrackEventSequence()
        # the current moment within the tab being edited. 
        self.active_moment = 0
        # for visual placement 
        self.presentation_column = self.FIRST_NOTE_COLUMN
        

    def getPresCol(self) -> int:
        return self.presentation_column

    def setPresCol(self, column: int):
        self.presentation_column = column 

    def createTabEvent(self, inherit=None) -> TabEvent:
        te = TabEvent(len(self.tuning))
        if inherit:
            te.note_duration = inherit.note_duration
            te.dynamic = inherit.dynamic
            te.legato = inherit.legato
            te.staccato = inherit.stacatto
            te.triplet = inherit.triplet
            te.quintuplet = inherit.quintuplet
        return te

    def computeMidiCode(self, te: TabEvent):
        raise FutureWarning("TODO: compute midi code based on tuning")

    def setTuning(self, tuning):
        self.tuning = tuning

    def isTheActivateMomentTheLastMoment(self):
        s : TrackEventSequence = self.sequence
        m = self.active_moment
        # look ahaed to the next moment
        evtList = s.data.get(m+1)
        if not evtList:
            return True
        # there is an edge case where the only thing that is there is a measure
        for evt in evtList:
            if isinstance(evt, TabEvent):
                return False
        # we made it here and althrough there was on more moment there
        # was no new tab. therefore we are actually at the end 
        return True 

        
    def getMoment(self):
        return self.active_moment

    def setMoment(self, moment):
        self.active_moment = moment

    def getTabEvent(self, moment=None) -> TabEvent:
        """
        get the tablature event for a given beat  
        """
        if not moment:
            moment = self.active_moment
        teList = self.sequence.get(moment)
        if teList:
            for te in teList:
                if isinstance(te, TabEvent):
                    return te
        
        raise ValueError("No track event for beat value %d" % moment)

    def getSequence(self) -> TrackEventSequence:
        return self.sequence
