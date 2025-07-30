"""
Controller for the current active editor.

Edits selected track from the navigator widget. Each
track is displayed as a TrackView widget that allows
for track events to be rendered.  
"""
import logging
import uuid
from PyQt6.QtCore import Qt

from services.redoUndo import RedoUndoProcessor
from view.config import EditorKeyMap
from view.editor.pastebuffer import PasteBufferSingleton
from view.events import Signals, EditorEvent, StringBendEvent
from models.track import Track
from view.editor.trackEditorView import TrackEditorView
from util.keyprocessor import KeyProcessor



class EditorController:

    def _ready(self):
        return self.track_editor_view and self.track_model
    

    def update(self, tmodel: Track | None, editor: TrackEditorView | None):
        """ 
        Called in response for when a track has been activated to render a score
        for that track.
        """
        if tmodel and editor:
            # track editing session id used for undo/redo
            tmodel.track_edit_id = str(uuid.uuid4())
            editor.set_track_model(tmodel)
            
    def add_model(self, evt: EditorEvent):
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor_view)
        if self.track_editor_view and self.track_model:
            self.track_editor_view.setFocus()

    def add_editor(self, evt: EditorEvent):
        self.track_editor_view = evt.track_editor

    def set_editor(self, tev: TrackEditorView):
        self.track_editor_view = tev    


    def keyboard_event(self, evt: EditorEvent):

        tedit : TrackEditorView | None = self.track_editor_view
        tmodel : Track | None = self.track_model
        key = evt.key

        if not tedit: return
        if not tmodel: return   

        paste_buffer = PasteBufferSingleton()
        if not evt.control_key_pressed and not paste_buffer.isEmpty():
            paste_buffer.clear()

        # Check for arrow keys
        if key == Qt.Key.Key_Up:
            tedit.arrow_up_key()
        elif key == Qt.Key.Key_Down:
            tedit.arrow_down_key()
            #self._updown_key(self.track_model, -1)
        elif key == Qt.Key.Key_Left:
            tedit.arrow_left_key(evt.control_key_pressed)
        elif key == Qt.Key.Key_Right:
            tedit.arrow_right_key(evt.control_key_pressed)
        elif key == Qt.Key.Key_Insert:
            tedit.insert_key()   
        elif key == Qt.Key.Key_Delete:
            tedit.delete_key()
        else:
            # get the tab event at the current moment
            #te : TabEvent = tmodel.getTabEvent()
            (tab_event, _) = tmodel.current_moment()

            # use the key to update the tablature cursor
            self.key_proc.proc(key, tab_event) 

            # render the updated tab event model.
            tedit.current_tab_event_updated()
            
        
    def tuning_change(self, evt: EditorEvent):
        tedit : TrackEditorView | None = self.track_editor_view
        if evt.tuning and self.track_model and tedit:
            self.track_model.tuning = evt.tuning 
            tedit.update()
 
    def measure_clicked(self, evt: EditorEvent):
        pass

    def string_bend_event(self, evt: EditorEvent):
        be = evt.bend_event 
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view

        if be and tmodel and tedit:
            # update the Note(s) of the current moment 
            (tab_event, _) = tmodel.current_moment()

            tab_event.pitch_changes = be.pitch_changes
            tab_event.pitch_range = be.pitch_range
            tab_event.pitch_bend_active = True

            # render the updated tab event model.
            tedit.current_tab_event_updated()


    def toggle_measure_start_repeat(self, evt: EditorEvent):
        tedit : TrackEditorView | None = self.track_editor_view
        if tedit:
            tedit.toggle_measure_start_repeat()
            
    def toggle_measure_end_repeat(self, evt: EditorEvent):
        tedit : TrackEditorView | None = self.track_editor_view
        if tedit:
            tedit.toggle_measure_end_repeat()


    def propagate_undo_redo_model_change(self, track: Track):
        assert(self.track_editor_view is not None)
        self.rup.disable_updates()
        self.track_model = track 
        self.track_editor_view.set_track_model(self.track_model)
        self.rup.enable_updates()

    def undo_event(self, evt: EditorEvent): 
        new_model = self.rup.undo(self.track_model)
        if new_model:
            self.propagate_undo_redo_model_change(new_model)    

    def redo_event(self, evt: EditorEvent): 
        new_model = self.rup.redo(self.track_model)
        if new_model:
            self.propagate_undo_redo_model_change(new_model)    


    dispatch = {
        EditorEvent.ADD_MODEL: add_model,
        EditorEvent.ADD_TRACK_EDITOR: add_editor,
        EditorEvent.KEY_EVENT: keyboard_event,
        EditorEvent.TUNING_CHANGE: tuning_change,
        EditorEvent.MEASURE_CLICKED: measure_clicked,
        EditorEvent.BEND_EVENT: string_bend_event,
        EditorEvent.MEASURE_REPEAT_START_KEY: toggle_measure_start_repeat,
        EditorEvent.MEASURE_REPEAT_END_KEY: toggle_measure_end_repeat,
        EditorEvent.UNDO_EVENT: undo_event,
        EditorEvent.REDO_EVENT: redo_event
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
        self.rup = RedoUndoProcessor()
        self.keymap = EditorKeyMap()
        self.track_model = None
        self.track_editor_view = None
        # track model -> cursor
        self.key_proc = KeyProcessor()
        self.sequence_renderer = None
        
        Signals.editor_event.connect(self.editor_event)
