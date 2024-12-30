from models.track import StaffEvent, TabEvent, Track, MeasureEvent, TrackEventSequence
from view.editor.trackEditor import TrackEditor
import logging


class SequenceRenderer:
    def __init__(self, tmodel: Track, teditor: TrackEditor):
        self.model = tmodel
        self.editor = teditor
        # what column in the grid is presenting tab event data for 
        # a given moment in the staff.
        self.moment_pres_column = {}

    def move_cursor_to_next_momement(self):
        moment = self.model.getMoment()
        seq : TrackEventSequence = self.model.getSequence()
        try:
            (moment,_) = seq.search(moment+1,seq.BACKWARD,seq.TAB_EVENT)
            assert(moment in self.moment_pres_column)
            col = self.moment_pres_column[moment]
            self.editor.move_cursor(col)
            self.model.setPresCol(col)
            self.model.setMoment(moment)
        except:
            pass     

    def move_cursor_to_prior_tab(self):
        moment = self.model.getMoment()
        seq : TrackEventSequence = self.model.getSequence()
        try:
            (moment,_) = seq.search(moment-1,seq.BACKWARD,seq.TAB_EVENT)
            assert(moment in self.moment_pres_column)
            col = self.moment_pres_column[moment]
            self.editor.move_cursor(col)
            self.model.setPresCol(col)
            self.model.setMoment(moment)
        except:
            pass     

        """
        logging.debug(f"moving cursor backward from moment {moment}")
        if moment > 0:
            moment -= 1
            assert(moment in self.moment_pres_column)
            col = self.moment_pres_column[moment]
            self.editor.move_cursor(col)
            self.model.setPresCol(col)
            self.model.setMoment(moment)
        """    

    def render_update_tab(self, te: TabEvent):
        seq = self.model.getSequence()
        # render fret number
        self.editor.drawFretValue(
            self.model.getPresCol(), te.string, te.fret[te.string])
        # update the toolbar if this was a duration/dynamic change
        self.editor.setToolbar(te)
        # update staff notation, get the active staff header
        # which has the cleff and key (sharps and flats)
        staff_event = seq.getActiveStaff(self.model.getMoment())
        if staff_event:
            # render staff: notes, chords, rests etc.
            self.editor.drawStaffEngraving(staff_event,
                                           te, self.model.getPresCol(), self.model.tuning)

    def append_tab_event(self):
        """ 
        Append a tablature event to the end of the staff

        If there are enough beats in the measure add the new tab event. If 
        adding this tab event consumes the number of beats in a measure then add
        a measure event. If the are not enough beats then replace the tab event with 
        one that fits the number of beats, add an end of measure then add a tab
        event to the next measure with the overflow duration.
        """
        seq = self.model.getSequence()
        staff_event = seq.getActiveStaff(self.model.getMoment())
        (measure_moment, measure_event) = \
            seq.search(self.model.getMoment(), seq.BACKWARD, seq.MEASURE_EVENT)
        current_moment = self.model.getMoment()

        ts = staff_event.compute_timespec()  # type: ignore
        beats_in_measure = ts.beats_per_measure * ts.beat_duration

        te = self.model.getTabEvent()
        new_te = te.clone()

        # compute how many beats exist from the start of the measure 
        beat_total = 0
        for moment in range(measure_moment, current_moment+1):
            beat_total += seq.getBeats(moment, ts.beat_duration)

        # are we at the end of this measure?
        if beat_total == beats_in_measure:
            moment = current_moment + 1
            col = self.model.getPresCol() + 2 # skip over measure
            seq.add(moment, new_te)

            self.editor.drawBlankSelectRegion(new_te, col, new_te.string)
            self.moment_pres_column[moment] = col

            self.model.setPresCol(col)
            self.model.setMoment(moment)
            return

        beat_total += new_te.beats(ts.beat_duration)    
        beat_total_before_current = beat_total

        if beat_total < beats_in_measure:
            # simple case we have enough beats to simply draw a new moment
            moment = current_moment + 1
            col = self.model.getPresCol() + 1
            seq.add(moment, new_te)

            self.editor.drawBlankSelectRegion(new_te, col, new_te.string)
            self.moment_pres_column[moment] = col

            self.model.setPresCol(col)
            self.model.setMoment(moment)

        elif beat_total == beats_in_measure:
            # simple case we have enough beats to simply draw a new moment
            moment = current_moment + 1

            new_measure = MeasureEvent()
            new_measure.measure_number = measure_event.measure_number + 1
            seq.add(moment+1, new_measure)
            seq.add(moment, new_te)

            col = self.model.getPresCol() + 1

            self.moment_pres_column[moment] = col
            self.editor.drawBlankSelectRegion(new_te, col, new_te.string)

            col += 1
            self.editor.drawMeasure(new_measure.measure_number, col)
            col += 1

            self.model.setPresCol(col)
            self.model.setMoment(moment)
        else:
            # we need two notes/codes/rests to implement the duration
            # one on the left side of the measure and the other on the right.
            left_b = beat_total_before_current - beats_in_measure 
            right_b = beat_total - beats_in_measure
 
            left_te = new_te.clone_from_beats(left_b, ts.beat_duration) 
            right_te = new_te.clone_from_beats(right_b, ts.beat_duration)

            new_measure = MeasureEvent()
            new_measure.measure_number = measure_event.measure_number + 1

            moment = current_moment + 1
 
            # replace current tab events
            seq.remove(moment, new_te)
            seq.add(moment, left_te)

            # add measure
            seq.add(moment+1, new_measure)

            # add an 'overflow' tab event
            right_te.tied_notes = left_te.fret
            seq.add(moment+1, right_te)  

            col = self.model.getPresCol() + 1

            self.moment_pres_column[moment] = col
            self.editor.drawBlankSelectRegion(left_te, col, left_te.string)
            col += 1

            self.editor.drawMeasure(new_measure.measure_number, col)
            col += 1

            self.moment_pres_column[moment+1] = col
            self.editor.drawBlankSelectRegion(right_te, col, right_te.string)
            
            self.model.setPresCol(col)
            self.model.setMoment(moment+1)
             
            
    def updown_cursor(self, inc: int):
        tc = self.model.getTabEvent()
        nstring = len(self.model.tuning)

        # change the string we are pointing to
        tc.string = (tc.string - inc) % nstring

        # move the rectangle select box on the tableture
        self.editor.drawSelectRegion(self.model.getPresCol(), tc.string)

    def initialize(self):
        """
        If the track is empty, insert a default Staff and a rest 
        in the tablature. If it isn't then render the track.
        """
        seq = self.model.getSequence()
        if seq.isEmpty():
            staff = StaffEvent()
            # add a default staff
            seq.add(0, staff)
            # create a empty tab event, set the presentation column to 1
            te: TabEvent = self.model.createTabEvent()
            seq.add(0, te)
            me = MeasureEvent()
            seq.add(0, me)
            # set the active moment to the beginning
            self.model.setMoment(0)

            # now render
            self.editor.drawHeader(staff, 0)
            self.editor.drawFirstMeasure(me.measure_number, 1)
            self.model.setPresCol(2)
            
            self.moment_pres_column[0] = 2
            num_str = len(self.model.tuning)-1
            self.editor.drawBlankSelectRegion(
                te, self.model.getPresCol(), num_str)

        else:
            # TODO.
            # render a previously saved track.
            pass
