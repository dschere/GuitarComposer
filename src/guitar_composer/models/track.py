import copy
import uuid

from guitar_composer.models.measure import TUPLET_DISABLED, Measure, TimeSig, TabEvent 
from typing import Callable, List, Optional, Tuple
from guitar_composer.models.effect import Effects
from guitar_composer.music.constants import Dynamic
from guitar_composer.music.durationtypes import QUARTER
from guitar_composer.services.effectRepo import EffectRepository

from guitar_composer.models.filterGraph import FilterGraph


class MomentCursor:
    """Cursor for sequentially traversing TabEvents across track measures."""

    def __init__(self, t : 'Track'):
        """Initialize a MomentCursor bound to the given Track instance.

        Args:
            t: Track instance to traverse.
        """
        self.t = t
        self.current_measure = -1
        self.current_tab_event = -1

    def first(self) -> TabEvent:
        """Move cursor to the current track cursor position and return the active TabEvent."""
        self.current_measure = self.t.current_measure
        m = self.t.measures[self.current_measure]
        self.current_tab_event = m.current_tab_event
        return m.tab_events[self.current_tab_event]
    
    def start_of_previous_measure(self):
        """Move cursor to the beginning of the previous measure and return its first TabEvent."""
        if self.current_measure > 0:
            self.current_measure -= 1
        self.current_tab_event = 0

        m = self.t.measures[self.current_measure]
        return m.tab_events[self.current_tab_event]

    
    def next(self) -> TabEvent | None:
        """Advance cursor to the next TabEvent across measure boundaries or return None if at end."""
        self.current_tab_event += 1
        m = self.t.measures[self.current_measure]
        if self.current_tab_event < len(m.tab_events):
            return m.tab_events[self.current_tab_event]
        else:
            self.current_tab_event = -1
            self.current_measure += 1
            if self.current_measure < len(self.t.measures):
                return self.next()
        # no more tab events return None

    


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
    
    def sync_measure_structure(self, other: 'Track'):
        """ 
        Make the measure structure of this track the same as the 
        'other' track. If the corresponding measure does not exist 
        add one with rests that match the notes in the 'other'
        track.
        """
        for (i,m) in enumerate(other.measures):
            if i > len(self.measures):
                new_m = copy.deepcopy(m)
                for te in new_m.tab_events:
                    te.fret = [-1] * te.num_gstrings
                self.measures.append(new_m)    
    
    def _reassemble(self, teList: List[TabEvent], ts: TimeSig, m_num: int):
        """
        Reassemble measures starting with the measure 'm_num'  
        """
        beats = 0
        self.measures[m_num].tab_events = []
        for te in teList:
            b = te.beats(ts.beat_duration())
            if beats+b <= ts.beats_per_measure:
                self.measures[m_num].tab_events.append(te.clone())
                beats += b
            else:
                m_num += 1
                beats = b
                if m_num < len(self.measures):
                    self.measures[m_num].tab_events = [te.clone()]
                    _ts = self.measures[m_num].timesig
                    if _ts is not None:
                        ts = _ts
                else:
                    m = Measure(measure_number=m_num+1)
                    self.measures.append(m)
                    self.measures[m_num].tab_events = [te.clone()]

    def remove_tab_events(self, remList: List[TabEvent]):
        """Remove specified TabEvents from track measures and reassemble the measure layout.

        Args:
            remList: List of TabEvent objects to remove.
        """
        if len(remList) == 0: return 

        uids = set([te.uuid for te in remList])
        teList = []
        for m in self.measures:
            for te in m.tab_events:
                if te.uuid not in uids:
                    teList.append(te)

        ts, _, _, _ = self.getMeasureParams(self.measures[0])
        m_num = 0
        self._reassemble(teList, ts, m_num)

        # re-assign current measure, tab if needed.
        if self.current_measure >= len(self.measures):
            self.current_measure = len(self.measures)-1
        m = self.measures[self.current_measure]
        if m.current_tab_event >= len(m.tab_events):
            m.current_tab_event = len(m.tab_events) - 1

    def disable_tuplet_group_if_needed(self):
        "Note: This function is meant to be called in conjunction with a delete tab"
        cursor = MomentCursor(self)
        te = cursor.first()

        if te.tuplet_group_id is not None:
            gid = te.tuplet_group_id
            end_measure = cursor.current_measure + 1

            te = cursor.start_of_previous_measure()
            while te is not None and cursor.current_measure < end_measure:
                if te.tuplet_group_id is not None and  te.tuplet_group_id == gid:
                    te.tuplet_group_id = None 
                    te.tuplet_code = TUPLET_DISABLED
                    te.tuplet_selected_enabled = True
                te = cursor.next()           


    def tuplet_alteration(self, code, beats) -> bool:
        """Convert or insert tuplet groups (e.g. triplets, quintuplets) starting at the current cursor position.

        Args:
            code: Tuplet code key from TupletTypes.
            beats: Number of beats spanned by the tuplet.

        Returns:
            True if alteration was applied, False otherwise.
        """
        
        # if current -> number of beats tab events are rests then
        # delete them from the track we can simply replace with 
        # tuples, if there are any non rests then this operation 
        # is an insert operation and the user will have to fix 
        # the measure.
        changed = True
        
        cursor = MomentCursor(self)
        first_te = cursor.first()
        gid = str(uuid.uuid4())

        if first_te.tuplet_code == code:
            return False #-> no alteration took place
        elif first_te.tuplet_code != TUPLET_DISABLED:
            # clear tuplet code for existing tuplet and triplet
            # and then recompute.
            cursor2 = MomentCursor(self)
            first_te = cursor2.first()
            count = first_te.tuplet_code 
            first_te.tuplet_code = TUPLET_DISABLED
            first_te.tuplet_selected_enabled = True
            count -= 1
            while count > 0:
                tab = cursor2.next()
                if tab is not None:
                    tab.tuplet_code = TUPLET_DISABLED
                    tab.tuplet_selected_enabled = True
                    count -= 1
            

        ref_tab = first_te.clone()
        ref_tab.tuplet_code = code 

        ref_dur = first_te.duration
        uniform_duration = True 
        exiting_within_beats = [first_te]
        total_duration = first_te.duration 
        exist_i = 0

        while total_duration < beats and uniform_duration:
            tab = cursor.next()
            if tab is None:
                uniform_duration = False
            elif tab.duration == ref_dur:
                total_duration += tab.duration 
                exiting_within_beats.append(tab)
            else:
                uniform_duration = False

        insList = []
        for i in range(0,code):
            if uniform_duration and exist_i < len(exiting_within_beats):
                te = exiting_within_beats[exist_i]
                exist_i += 1
                te_n = te.clone()
                te_n.tuplet_code = code
                te_n.tuplet_selected_enabled = i == 0
                # associate this tab with a tuplet group id
                te_n.tuplet_group_id = gid

                insList.append(te_n)
            else:
                te_n = ref_tab.clone()
                te_n.tuplet_selected_enabled = False
                # associate this tab with a tuplet group id
                te_n.tuplet_group_id = gid

                insList.append(te_n)

        c_te, c_m = self.current_moment()
        ts, _, _, _ = self.getMeasureParams(c_m)

        teList = c_m.tab_events[:c_m.current_tab_event] + insList + c_m.tab_events[c_m.current_tab_event:]
        midx = self.current_measure + 1
        while midx < len(self.measures):
            teList += self.measures[midx].tab_events
            midx += 1
        m_num = self.current_measure

        if uniform_duration:
            while len(exiting_within_beats) > 0:
                te = exiting_within_beats.pop()
                idx = teList.index(te)
                del teList[idx]

        # adjust the current tab event and current measure. 
        self._reassemble(teList, ts, m_num)
            
        return changed

    def insert_tab_events(self, insList: List[TabEvent]):
        """Insert a list of TabEvents at the current cursor position and reassemble subsequent measures.

        Args:
            insList: List of TabEvent objects to insert.
        """
        if len(insList) == 0: return

        c_te, c_m = self.current_moment()
        ts, _, _, _ = self.getMeasureParams(c_m)

        teList = c_m.tab_events[:c_m.current_tab_event] + insList + c_m.tab_events[c_m.current_tab_event:]
        midx = self.current_measure + 1
        while midx < len(self.measures):
            teList += self.measures[midx].tab_events
            midx += 1
        m_num = self.current_measure

        # adjust the current tab event and current measure. 
        self._reassemble(teList, ts, m_num)

    def getMeasureParams(self, m : Measure) -> Tuple[TimeSig, int, str, str]:
        """Retrieve the effective TimeSig, BPM, key, and clef settings governing a given measure.

        Args:
            m: Target Measure to evaluate.

        Returns:
            Tuple of (TimeSig, bpm, key, cleff).
        """
        ts = self.measures[0].timesig
        bpm = self.measures[0].bpm
        key = self.measures[0].key
        cleff = self.cleff 
        from guitar_composer.view.editor.glyphs.common import TREBLE_CLEFF

        if ts is None:
            ts = TimeSig() 
        if bpm is None:
            bpm = 120 
        if key is None:
            key = "C"
        if cleff is None:
            cleff = TREBLE_CLEFF

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

    def __setstate__(self, state):
        """Restore unpickled Track state and apply schema compatibility defaults."""
        # support migration
        self.__dict__.update(state)
        
        if not hasattr(self, "drum_track"):
            self.drum_track = False

    def __init__(self, cleff = None):
        """Initialize a Track instance with default tuning, starter measure, and clef.

        Args:
            cleff: Optional clef glyph identifier (defaults to TREBLE_CLEFF).
        """
        self.track_edit_id = ""
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
        self.drum_track = False

        # create a default Measure as a starter
        # 4/4 time, bpm 120 and in the key of C
        from guitar_composer.view.editor.glyphs.common import TREBLE_CLEFF

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
        #self.effects = EffectRepository().create_effects()
        self.effects : Effects | None = None

    def append_measure(self, **kwargs):
        """Create and append a new blank measure to the end of the track.

        Args:
            **kwargs: Optional measure configuration parameters.

        Returns:
            The newly created Measure.
        """
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
        """Remove the current measure from the track and renumber remaining measures."""
        if len(self.measures) > 1:
            # preserve the staff header information of the first measure 
            first_measure = copy.deepcopy(self.measures[0])
            
            del self.measures[self.current_measure]
            if self.current_measure >= len(self.measures):
                self.current_measure = len(self.measures) - 1
            for (mn, m) in enumerate(self.measures):
                m.measure_number = mn + 1 
            self.measures[0].bpm = first_measure.bpm
            self.measures[0].key = first_measure.key
            self.measures[0].cleff = first_measure.cleff
            self.measures[0].timesig = first_measure.timesig
            self.measures[0].staff_changes = True 


    def current_moment(self) -> Tuple[TabEvent, Measure]:
        """Return the active (TabEvent, Measure) tuple at the current track cursor position."""
        m = self.measures[self.current_measure] 
        return (m.tab_events[m.current_tab_event], m)

    def get_measure(self, from_current=0):
        """Return the Measure offset relative to the current measure, or None if out of range.

        Args:
            from_current: Relative integer offset from the current measure index.
        """
        i = self.current_measure + from_current 
        if i >= 0 and i < len(self.measures):
            return self.measures[i]    

    def find_tab_measure(self, tab_event: TabEvent) -> Measure | None:
        """Find the Measure containing the specified TabEvent by matching UUID.

        Args:
            tab_event: TabEvent to locate.
        """
        for m in self.measures:
            if tab_event.uuid in [te.uuid for te in m.tab_events]:
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
    
    def get_filter_graph(self, te: TabEvent) -> FilterGraph | None:
        """Retrieve the effective FilterGraph active up to the specified TabEvent.

        Args:
            te: TabEvent to evaluate.
        """
        fg = None
        for m in self.measures:
            for t in m.tab_events:
                if t.fg is not None:
                    fg = t.fg
                if t is te:
                    return fg      
    
    def skip_measure(self):
        "skip the current measure to next one"
        if (self.current_measure+1) < len(self.measures):
            self.current_measure += 1
            m = self.measures[self.current_measure]
            m.current_tab_event = 0

    def previous_measure(self):
        """Move the track cursor to the start of the previous measure if not at the beginning."""
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
        """Move cursor to the previous TabEvent across measure boundaries and return (TabEvent, Measure)."""
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
        """Set the active cursor position to a specific measure and tab event index.

        Args:
            measure: Target measure index.
            tab: Target tab event index within the measure.
        """
        if measure < len(self.measures):
            self.current_measure = measure
            m = self.measures[self.current_measure]
            if tab < len(m.tab_events):
                m.current_tab_event = tab
        
    def is_last_moment(self):
        """Return True if the track cursor is positioned on the final TabEvent of the final measure."""
        if self.current_measure == (len(self.measures)-1):
            m = self.measures[self.current_measure] 
            if m.current_tab_event == (len(m.tab_events)-1):
                return True
        return False

    def createTabEvent(self, inherit=None) -> TabEvent:
        """Create a new TabEvent matched to this track's tuning, optionally inheriting properties.

        Args:
            inherit: Optional TabEvent from which duration, dynamics, and articulation are copied.

        Returns:
            The created TabEvent.
        """
        te = TabEvent(len(self.tuning))
        if inherit:
            te.duration = inherit.duration
            te.dynamic = inherit.dynamic
            te.legato = inherit.legato
            te.staccato = inherit.stacatto
        return te

    def computeMidiCodes(self, te: TabEvent):
        """Compute absolute MIDI note numbers for fret positions based on track tuning."""
        raise FutureWarning("TODO: compute midi code based on tuning")

    def setTuning(self, tuning):
        """Update track tuning definition with a new list of open-string pitch names.

        Args:
            tuning: List of string pitch names (e.g. ['E4', 'B3', 'G3', 'D3', 'A2', 'E2']).
        """
        self.tuning = tuning

if __name__ == '__main__':
    t = Track(6)
    te = t.measures[0].tab_events[0]
    te.duration = 0.5

    t.measures[0].tab_events = []
    for i in range(0,8):
        t.measures[0].tab_events.append( te.clone() )

    t.tuplet_alteration(5,2)
    print(t.measures)
    for m in t.measures:
        print([te.tuplet_code for te in m.tab_events])
