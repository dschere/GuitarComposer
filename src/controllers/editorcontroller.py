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

class Cursor:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.glyph = None
        self.text = ""


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
            # if fret value, add a note for this chord
            #  ...

            # change the string we are pointing to
            tc.string = (tc.string - inc) % nstring

            # move the rectangle select box on the tableture
            te.setSelectRegion(tc.presentation_col, tc.string)

            # clear the fret value
            #tc.fret = -1


    def update(self, tmodel: Track | None, editor: TrackEditor | None):
        if tmodel and editor:
            # get the current staff value from the model
            seq = tmodel.getSequence()
            tcur = tmodel.getTabEvent()

            # in the caseof an empty track sequence add a default staff
            staff = StaffEvent()
            evtList = seq.get(0)
            if not evtList:
                seq.add(0, staff)
            else:
                # otherwise find the existing staff
                for tevt in evtList:
                    if isinstance(tevt, StaffEvent):
                        staff = tevt
                        break
            # set the staff header        
            editor.setHeader(staff)
            #TODO set the remaining tablature 
            # ...
             
            # set the box that indicates where key events will be
            # applied on the staff. 
            editor.setBlankSelectRegion(tcur, tcur.presentation_col)

    def add_model(self, evt: EditorEvent):
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor)
        if self.track_editor:
            self.track_editor.setFocus()

    def add_editor(self, evt: EditorEvent):
        self.track_editor = evt.track_editor

    def update_cursor(self):
        tedit : TrackEditor | None = self.track_editor
        if tedit:
            tmodel : Track = self.track_model
            te : TabEvent = tmodel.getTabEvent()
            seq : TrackEventSequence = tmodel.getSequence()
            tedit.setFretValue(te.presentation_col, te.string, te.fret[te.string])
            # update the toolbar if this was a duration/dynamic change
            # which has the cleff and key (sharps and flats)
            staff_event = seq.getActiveStaff(self.cursor_beat_pos)
            if staff_event:
                # render staff: notes, chords, rests etc.
                tedit.renderStaffEngraving(staff_event, tmodel, te.presentation_col)

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
            tedit.setFretValue(te.presentation_col, te.string, te.fret[te.string])
            # update the toolbar if this was a duration/dynamic change
            tedit.setToolbar(te)
            # update staff notation, get the active staff header
            # which has the cleff and key (sharps and flats)
            staff_event = seq.getActiveStaff(self.cursor_beat_pos)
            if staff_event:
                # render staff: notes, chords, rests etc.
                tedit.renderStaffEngraving(staff_event, tmodel, te.presentation_col)
        
    def tuning_change(self, evt: EditorEvent):
        if evt.tuning and self.track_model:
            self.track_model.tuning = evt.tuning
 

    dispatch = {
        EditorEvent.ADD_MODEL: add_model,
        EditorEvent.ADD_TRACK_EDITOR: add_editor,
        EditorEvent.KEY_EVENT: keyboard_event,
        EditorEvent.TUNING_CHANGE: tuning_change
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
        self.cursor_beat_pos = 0

        Signals.editor_event.connect(self.editor_event)
