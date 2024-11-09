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
from models.track import Track, StaffEvent
from view.editor.trackEditor import TrackEditor


class Cursor:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.glyph = None
        self.text = ""


class EditorController:

    def _ready(self):
        return self.track_editor and self.track_model

    def _up_key(self, tmodel: Track | None):
        if tmodel:
            tc = tmodel.getTabCursor()
            nstring = len(tmodel.tuning)
            # if fret value, add a note for this chord
            #  ...

            # change the string we are pointing to
            tc.string = (tc.string - 1) % nstring

            # move the rectangle select box on the tableture

            # clear the fret value
            tc.fret = None

    def _down_key(self, tmodel: Track | None):
        if tmodel:
            tc = tmodel.getTabCursor()
            nstring = len(tmodel.tuning)
            # if fret value, add a note for this chord
            #  ...

            # change the string we are pointing to
            tc.string = (tc.string + 1) % nstring

            # move the rectangle select box on the tableture

            # clear the fret value
            tc.fret = None

    def update(self, tmodel: Track | None, editor: TrackEditor | None):
        if tmodel and editor:
            # get the current staff value from the model
            seq = tmodel.getSequence()
            staff = StaffEvent()
            evtList = seq.get(0)
            if not evtList:
                seq.add(0, staff)
            else:
                for tevt in evtList:
                    if isinstance(tevt, StaffEvent):
                        staff = tevt
                        break
            editor.setHeader(staff)

    def add_model(self, evt: EditorEvent):
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor)

    def add_editor(self, evt: EditorEvent):
        self.track_editor = evt.track_editor

    def keyboard_event(self, evt: EditorEvent):
        key = evt.key
        # Check for arrow keys
        if key == Qt.Key.Key_Up:
            self._up_key(self.track_model)
        elif key == Qt.Key.Key_Down:
            self._down_key(self.track_model)
        elif key == Qt.Key.Key_Left:
            pass
        elif key == Qt.Key.Key_Right:
            pass

    dispatch = {
        EditorEvent.ADD_MODEL: add_model,
        EditorEvent.ADD_TRACK_EDITOR: add_editor,
        EditorEvent.KEY_EVENT: keyboard_event
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

        Signals.editor_event.connect(self.editor_event)
