"""
Controller for the current active editor.

Edits selected track from the navigator widget. Each
track is displayed as a TrackView widget that allows
for track events to be rendered.  
"""
import logging
from PyQt6.QtCore import Qt

from view.editor.sequenceRenderer import SequenceRenderer
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
            print(f"nstring = {nstring}")
            # change the string we are pointing to
            tc.string = (tc.string - inc) % nstring

            # move the rectangle select box on the tableture
            te.drawSelectRegion(tmodel.getPresCol(), tc.string)

    def update(self, tmodel: Track | None, editor: TrackEditor | None):
        """ 
        Called in response for when a track has been activated to render a score
        for that track.
        """
        if tmodel and editor:
            self.sequence_renderer = SequenceRenderer(tmodel, editor)
            self.sequence_renderer.initialize()
            
    def add_model(self, evt: EditorEvent):
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor)
        if self.track_editor and self.track_model:
            self.track_editor.setFocus()

    def add_editor(self, evt: EditorEvent):
        self.track_editor = evt.track_editor

    def key_right_handler(self):
        if self.sequence_renderer and self.track_model:
            if self.track_model.isTheActivateMomentTheLastMoment():
                self.sequence_renderer.append_tab_event() 
            else:
                self.sequence_renderer.move_cursor_to_next_momement()

    def key_left_handler(self):
        if self.sequence_renderer:
            self.sequence_renderer.move_cursor_to_prior_tab()

    def keyboard_event(self, evt: EditorEvent):
        tedit : TrackEditor | None = self.track_editor
        tmodel : Track | None = self.track_model
        tm : SequenceRenderer | None = self.sequence_renderer
        key = evt.key

        if not tm:
            return 

        # Check for arrow keys
        if key == Qt.Key.Key_Up:
            tm.updown_cursor(1)
            #self._updown_key(self.track_model, 1)
        elif key == Qt.Key.Key_Down:
            tm.updown_cursor(-1)
            #self._updown_key(self.track_model, -1)
        elif key == Qt.Key.Key_Left:
            self.key_left_handler()
        elif key == Qt.Key.Key_Right:
            self.key_right_handler()
        elif tedit and tmodel:
            # get the tab event at the current moment
            te : TabEvent = tmodel.getTabEvent()
            # use the key to update the tablature cursor
            self.key_proc.proc(key, te) 
            self.sequence_renderer.render_update_tab(te)
        
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
        self.sequence_renderer = None
        
        Signals.editor_event.connect(self.editor_event)
