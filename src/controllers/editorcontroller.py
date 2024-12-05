"""
Controller for the current active editor.

Edits selected track from the navigator widget. Each
track is displayed as a TrackView widget that allows
for track events to be rendered.  
"""
import logging
from PyQt6.QtCore import Qt

from view.config import EditorKeyMap
from view.events import Signals, EditorEvent
from models.track import Track, StaffEvent, TabEvent, TrackEventSequence
from view.editor.trackEditor import TrackEditor
from util.keyprocessor import KeyProcessor


class EditorController:

    def _ready(self):
        return self.track_editor and self.track_model
    
    def _commit_fret_notes(self):
        pass

    def _updown_key(self, tmodel: Track | None, inc: int):
        if tmodel and self.track_editor:
            te : TrackEditor = self.track_editor 
            tc = tmodel.getTabEvent()
            nstring = len(tmodel.tuning)

            # change the string we are pointing to
            tc.string = (tc.string - inc) % nstring

            # move the rectangle select box on the tableture
            te.drawSelectRegion(tc.presentation_col, tc.string)

    def update(self, tmodel: Track | None, editor: TrackEditor | None):
        """ 
        Called in response for when a track has been activated to render a score
        for that track.
        """
        if tmodel and editor:
            # get the current staff value from the model
            seq = tmodel.getSequence()

            # in the case of an empty track sequence add a default staff
            # and a default TabEvent 
            staff = StaffEvent()
            evtList = seq.get(0)
            if not evtList:
                # add a default staff 
                seq.add(0, staff)
                # create a empty tab event, set the presentation column to 1
                te : TabEvent = tmodel.createTabEvent()
                seq.add(0, te) 
                # set the active beat to the beginning
                tmodel.setActiveBeat(0)
                
            else:
                # otherwise find the existing staff
                for tevt in evtList:
                    if isinstance(tevt, StaffEvent):
                        staff = tevt
                        break
            # set the staff header        
            editor.drawHeader(staff)
            editor.drawFirstMeasure(1,1)
            te.presentation_col = 2

            #TODO 
            # render entire track 
             
            #-- throw away code. 
            # set the box that indicates where key events will be
            # applied on the staff. 
            te = tmodel.getTabEvent()
            editor.drawBlankSelectRegion(te, te.presentation_col)

    def add_model(self, evt: EditorEvent):
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor)
        if self.track_editor:
            self.track_editor.setFocus()

    def add_editor(self, evt: EditorEvent):
        self.track_editor = evt.track_editor

    def key_right_handler(self):
        # get the current tab event
        # compute the beat pos, determine if we need to draw a new measure
        # if yes
        #    insert a measure divider
        # create a new one inheriting some information from current
        # compute column -> old column + 1 or 2 if new measure
        # insert new blank tab, position cursor on new tab.
        # update beat -> column table for quick lookup.  
        pass    

    def keyboard_event(self, evt: EditorEvent):
        tedit : TrackEditor | None = self.track_editor
        tmodel : Track | None = self.track_model
        key = evt.key
        # Check for arrow keys
        if key == Qt.Key.Key_Up:
            self._updown_key(self.track_model, 1)
        elif key == Qt.Key.Key_Down:
            self._updown_key(self.track_model, -1)
        elif key == Qt.Key.Key_Left:
            pass
        elif key == Qt.Key.Key_Right:
            pass
        elif tedit and tmodel:
            te : TabEvent = tmodel.getTabEvent()
            seq : TrackEventSequence = tmodel.getSequence()
 
            # use the key to update the tablature cursor
            self.key_proc.proc(key, te) 
            # render fret number
            tedit.drawFretValue(te.presentation_col, te.string, te.fret[te.string])
            # update the toolbar if this was a duration/dynamic change
            tedit.setToolbar(te)
            # update staff notation, get the active staff header
            # which has the cleff and key (sharps and flats)
            staff_event = seq.getActiveStaff(self.cursor_beat_pos)
            if staff_event:
                # render staff: notes, chords, rests etc.
                tedit.drawStaffEngraving(staff_event, te, te.presentation_col, tmodel.tuning)
        
    def tuning_change(self, evt: EditorEvent):
        if evt.tuning and self.track_model:
            self.track_model.tuning = evt.tuning
 
    def measure_clicked(self, evt: EditorEvent):
        print(evt.measure)

    dispatch = {
        EditorEvent.ADD_MODEL: add_model,
        EditorEvent.ADD_TRACK_EDITOR: add_editor,
        EditorEvent.KEY_EVENT: keyboard_event,
        EditorEvent.TUNING_CHANGE: tuning_change,
        EditorEvent.MEASURE_CLICKED: measure_clicked
    }

    def editor_event(self, evt: EditorEvent):
        func = self.dispatch.get(evt.ev_type)  # type: ignore
        if func:
            func(self, evt)  # type: ignore
        else:
            text = "Unsupported event type %d" % evt.ev_type
            logging.error(vars(evt))
            raise RuntimeError(text)

    def __init__(self):
        self.keymap = EditorKeyMap()
        self.track_model = None
        self.track_editor = None
        # track model -> cursor
        self.key_proc = KeyProcessor()

        # book keeping for the tab cursor 
        self.cursor_beat_pos = 0
        self.cursor_col_pos = TabEvent.FIRST_NOTE_COLUMN
        self.col_to_beat = {} 
        
        Signals.editor_event.connect(self.editor_event)
