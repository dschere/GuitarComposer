
from guitar_composer.music.constants import Dynamic
from typing import Dict, List, Tuple
from guitar_composer.music.durationtypes import (WHOLE, 
        HALF, QUARTER, SIXTEENTH, THIRTYSECOND, SIXTYFORTH)
from guitar_composer.models.effect import Effects 
from guitar_composer.models.filterGraph import FilterGraph, GraphNode

import logging
import math
import uuid
import copy
from collections import OrderedDict

class DynamicVariance:
    """Controls dynamic changes (velocity curves) across beats within a measure."""

    def __init__(self):
        """Initialize DynamicVariance with default pattern, duration, and tracking counters."""
        # set by user
        self.dynamic_pattern : List[int] = []
        self.duration = 1.0
        self.repeat_per_measure = True 
        self.enabled = True

        # these are for book keeping for the player
        self.beat_count = 0.0

    def isEnabled(self):
        """Return whether dynamic variance processing is enabled."""
        return self.enabled
    
    def setEnabled(self, e: bool):
        """Set whether dynamic variance processing is enabled."""
        self.enabled = e

    def reset(self):
        """Reset internal beat tracking accumulator to zero."""
        self.beat_count = 0.0
        
    def getDynamic(self, beats_per_measure: int, beats: float, default: int) -> int:
        """Calculate the next dynamic velocity value based on elapsed beat count.

        Args:
            beats_per_measure: Time signature beats per measure.
            beats: Duration of the current event in beats.
            default: Fallback dynamic velocity.

        Returns:
            Calculated dynamic velocity value.
        """
        d = default
        plen = len(self.dynamic_pattern)
        if self.enabled and plen > 0:
            units = int(self.beat_count / self.duration)
            if self.repeat_per_measure:
                units = units % beats_per_measure
            d = self.dynamic_pattern[units % plen]

            self.beat_count += beats 
            if self.beat_count > (plen * self.duration):
                self.beat_count -= (plen * self.duration)

            if self.repeat_per_measure and self.beat_count >= beats_per_measure:
                self.beat_count = 0.0

        return d
        
        

class TimeSig:
    """Represents a musical time signature (e.g. 4/4, 3/4, 6/8)."""

    def __init__(self):
        """Initialize a standard 4/4 TimeSig instance."""
        # number of beat notes per measure 
        self.beats_per_measure = 4
        # code identifying what the beat is 4
        # is queater note, 8 is an eight note 
        self.beat_note_id = 4

    def __eq__(self, other):
        """Check equality between this and another TimeSig instance."""
        if isinstance(other, TimeSig):
            return other.beats_per_measure == self.beats_per_measure and other.beat_note_id == self.beat_note_id
        return False


    def beat_duration(self):
        """Calculate the duration value corresponding to a single beat note."""
        return 4.0 / self.beat_note_id    

# number of notes, text label, number of beats 
TupletTypes = OrderedDict()

TupletTypes[3] = ("triplet", 1)
TupletTypes[5] = ("quintuplet", 2)
TupletTypes[6] = ("sextuplet", 2)
TupletTypes[7] = ("septuplet", 2)
TupletTypes[9] = ("nonuplet", 4)
TupletTypes[10] = ("decuplet", 4)
TupletTypes[11] = ("uncuplet", 4)
TupletTypes[12] = ("dodecuplet", 4)
TupletTypes[13] = ("tridecuplet", 4)

TUPLET_DISABLED = -1

class TabEvent:
    BEND_PERIODS = 13

    REST = 0
    NOTE = 1
    CHORD = 2

    def getTupletData(self) -> List[Tuple[int, str, int]]:
        """Return a list of available tuplet configurations (type code, label, beats)."""
        return [(tup_type, label, beats) for tup_type, (label, beats) in TupletTypes.items()]

    def setTupletCode(self, c : int):
        """Assign a tuplet code to this tab event.

        Args:
            c: Valid code key in TupletTypes.
        """
        assert c in TupletTypes
        self.tuplet_code = c 

    def getTupletCode(self):
        """Return the active tuplet code for this event, or TUPLET_DISABLED."""
        return self.tuplet_code
    
    def getTupletBeats(self) -> int:
        """Return the total number of beats allocated to the tuplet group this event belongs to."""
        (_, beats) = TupletTypes.get(self.tuplet_code, ('',0))
        return beats

    def classify(self):
        """Classify this tab event as REST, NOTE, or CHORD based on active frets."""
        result = self.REST
        for val in self.fret:
            if val != -1:
                result += 1
                if result == self.CHORD:
                    break
        return result
        
    def __setstate__(self, state):
        """Restore unpickled state with backwards-compatibility schema migrations."""
        # support migration
        self.__dict__.update(state)

        # Fix old data
        if not hasattr(self, 'fret_ypos'):
            self.note_ypos = [-1] * self.num_gstrings
        if type(self.tied_notes[0]) == type(-1):
            self.tied_notes = [False] * self.num_gstrings    
        if not hasattr(self, "actual_duration"):
            self.actual_duration = -1           
        if not hasattr(self,"tuplet_code"):
            self.tuplet_code = TUPLET_DISABLED
        if not hasattr(self,"fg"):
            self.fg = None
        if not hasattr(self,"fg_node_changes"):
            self.fg_node_changes = None


    # used to prevent selecting a tuplet while within a tuplet 
    def tuplet_option_enabled(self) -> bool:
        """Return whether tuplet modification is permitted on this event."""
        return getattr(self,"tuplet_selected_enabled",True)

    
    def toggle_tied(self):
        """Toggle the tied status of the note on the currently selected string."""
        if self.tied_notes[self.string]:
            self.tied_notes[self.string] = False
        else:
            self.tied_notes[self.string] = True

    def clone(self):
        """Create a detached deep copy of this TabEvent with a newly generated UUID."""
        r = copy.deepcopy(self)
        r.uuid = str(uuid.uuid4())
        r.effects = None
        return r
    
    def is_rest(self):
        """Return True if all strings are unfretted (-1), representing a rest."""
        return sum(self.fret) == (-1 * self.num_gstrings)
    
    def minimum_y_pos_for_tuplet_line(self):
        """Calculate the top vertical coordinate suitable for rendering a tuplet bracket or line."""
        rest_y = 140
        stem_size = 50 
        s = set(self.note_ypos)
        if -1 in s:
            s.remove(-1)
        if len(s) == 0:
            return rest_y 
        r = min(s)
        if r-stem_size < stem_size:
            return stem_size
        return r-stem_size

    def __init__(self, num_gstrings):
        """Initialize a TabEvent for an instrument with the specified number of strings.

        Args:
            num_gstrings: Number of instrument strings.
        """
        super().__init__()

        # because the player does a copy of the tab events we need
        # a uuid for the track.find_tab_measure to work.
        self.uuid = str(uuid.uuid4())

        self.duration = QUARTER
        self.string = num_gstrings - 1  # current string being edited
        self.fret = [-1] * num_gstrings  # current fret value
        self.tied_notes = [False] * num_gstrings

        self.note_ypos = [-1] * num_gstrings  
        self.tuplet_selected_enabled = True
        """ 
        tied_notes indicate that a note from a prevent tab event will 
        continue playing for a given string in this event. 

        Example (a hammer on the high E string while still playing two notes):

        Tablature D major hammer on D sus 4.
        -- 2 -- 3 
        -- 3 -- <3> << tied note
        -- 2 -- <2> << tied note
        -- 0 -- <0> << tied note. 
        """

        # visual representation in ornament widget 
        self.pitch_bend_active = False
        self.points = None 

        # pitch_changes -> (when_r, semitones)
        self.pitch_changes = []
        self.pitch_range = 2

        self.dotted = False
        self.double_dotted = False
    
        self.render_dynamic = False 
        self.dynamic = None
        self.dynamic_variance : DynamicVariance | None  = None

        # Index into TupletTypes, 0 indicates disabled. 
        self.tuplet_code = TUPLET_DISABLED

        self.legato : bool | None = None
        self.staccato : bool | None = None
        self.render_clear_articulation = False
        self.upstroke = False
        self.downstroke = False
        self.stroke_duration = SIXTEENTH
        self.stroke_duration_index : int | None = None
        self.effects : Effects | None = None
        self.fg : FilterGraph | None = None
        # this tab contains changes to another filter graph defined in a different tab 
        # event.
        self.fg_node_changes : Dict[str, GraphNode] | None = None

        self.num_gstrings = num_gstrings

        # tuplets such as triplets and quintuplets are all tagged as part of a group
        # if one tab event of that group is removed then all other members are marked as not
        # part of a tuplet. So you can have only two notes as part of triplet, or 4 in a quintuplet. 
        self.tuplet_group_id : str | None = None

        # normally computed by fret/string this is used as a placeholder while
        # loading midi from a file then arranging the string and fret number later.
        self.midi_codes = []

    def getDynamic(self):
        """Return the dynamic velocity setting for this event, defaulting to Dynamic.MF."""
        if self.dynamic:
            return self.dynamic
        return Dynamic.MF    

    def getEffects(self) -> Effects | None:
        """Return the Effects collection configured for this event."""
        return self.effects

    def setEffects(self, el : Effects):
        """Assign an Effects collection to this tab event."""
        self.effects = el

    def update(self, other):
        """Copy all instance attributes from another TabEvent instance into this one."""
        for k,v in vars(other).items():
            setattr(self,k,v) 

    def beats(self, beat_note_dur: float):
        """Calculate the total duration of this event in beats, factoring in dots and tuplets.

        Args:
            beat_note_dur: Duration of one beat note relative to a whole note.

        Returns:
            Computed beat duration rounded to 4 decimal places.
        """
        # example if 6/8 time, then beat_note_dur is 0.5 so 
        # a quater note (duration=1.0) is 2 beats.
        #beats = self.duration / (4.0 / beat_note_dur)
        beats = self.duration /  beat_note_dur
        if self.duration != WHOLE:
            if self.dotted:
                beats *= 1.5
            if self.double_dotted:
                beats *= 1.75
            if self.tuplet_code in TupletTypes:
                (_, tuplet_beats) = TupletTypes[self.tuplet_code]
                m = tuplet_beats / (0.5 * self.tuplet_code)
                beats *= m

        return round(beats, 4)



class Measure:
    """Represents a single measure in a musical track, containing ordered TabEvents."""

    def __init__(self, **kwargs):
        """Initialize a Measure instance with optional time signature, key, tempo, and repeat flags.

        Args:
            **kwargs: Optional measure parameters (timesig, bpm, key, start_repeat, end_repeat, repeat_count, measure_number).
        """
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
        """Insert a new TabEvent immediately after the current cursor index."""
        i = self.current_tab_event
        self.insert(tab_event, i)

    def insert(self, tab_event : TabEvent, i : int):
        """Insert a TabEvent at the specified index within this measure.

        Args:
            tab_event: The TabEvent to insert.
            i: Target insertion index.
        """
        if i >= 0 and i < len(self.tab_events):
            n = self.tab_events[:i] + [tab_event] + self.tab_events[i:]
            self.tab_events = n

    def remove_current(self):
        """Remove the TabEvent at the current cursor index and adjust the cursor position."""
        del self.tab_events[self.current_tab_event]
        self.current_tab_event = self.current_tab_event % len(self.tab_events)        

    def append(self, tab_event : TabEvent):
        """Append a TabEvent to the end of this measure."""
        self.tab_events.append(tab_event)        

    def delete(self, i : int):
        """Delete the TabEvent at index i if within bounds."""
        if i >= 0 and i < len(self.tab_events):
            del self.tab_events[i]

    def set_timespec(self, timespec : TimeSig):
        """Set the time signature for this measure."""
        self.timesig = timespec

    def set_cleff(self, cleff : str):
        """Set the clef for this measure."""
        self.cleff = cleff

    def update_beat_errmsg(self, ts: TimeSig):
        """Validate whether the total beat count of tab events matches the time signature.

        Args:
            ts: Active TimeSig governing this measure.
        """
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

