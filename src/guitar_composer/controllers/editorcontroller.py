"""
Controller for the current active editor.

Edits selected track from the navigator widget. Each
track is displayed as a TrackView widget that allows
for track events to be rendered.  
"""
import logging
from typing import List, Tuple
import uuid
import math
from PyQt6.QtCore import Qt

from guitar_composer.models.measure import TabEvent
from guitar_composer.services.redoUndo import RedoUndoProcessor
from guitar_composer.view.config import EditorKeyMap
from guitar_composer.view.editor.pastebuffer import PasteBufferSingleton
from guitar_composer.view.events import Signals, EditorEvent, StringBendEvent
from guitar_composer.models.track import Track
from guitar_composer.view.editor.trackEditorView import TrackEditorView
from guitar_composer.util.keyprocessor import KeyProcessor



class EditorController:

    def _ready(self):
        """Return True if both track editor view and track model are attached and ready."""
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
        """Attach a Track model to the editor and update the view display.

        Args:
            evt: EditorEvent carrying the track model.
        """
        self.track_model = evt.model
        self.update(self.track_model, self.track_editor_view)
        if self.track_editor_view and self.track_model:
            self.track_editor_view.setFocus()
            

    def add_editor(self, evt: EditorEvent):
        """Register the TrackEditorView component from an incoming EditorEvent.

        Args:
            evt: EditorEvent carrying the track editor view.
        """
        self.track_editor_view = evt.track_editor

    def set_editor(self, tev: TrackEditorView):
        """Set the active TrackEditorView instance directly.

        Args:
            tev: TrackEditorView instance.
        """
        self.track_editor_view = tev    


    def keyboard_event(self, evt: EditorEvent):
        """Handle keyboard navigation, editing, and note entry events within the active track.

        Args:
            evt: EditorEvent containing key press details and modifier flags.
        """
        tedit : TrackEditorView | None = self.track_editor_view
        tmodel : Track | None = self.track_model
        key = evt.key

        if not tedit: return
        if not tmodel: return   

        paste_buffer = PasteBufferSingleton()

        # if we are selecting text for a copy and paste
        # the control key must be pressed as well as left or right
        # keys, otherwise clear the cut/paste highlight.
        if evt.control_key_pressed and key in [Qt.Key.Key_Left,Qt.Key.Key_Right]:
            pass
        else:
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
            self.key_proc.proc(key, tab_event, tmodel) 

            # render the updated tab event model.
            tedit.current_tab_event_updated()
            
        
    def tuning_change(self, evt: EditorEvent):
        """Apply tuning changes to the current track and trigger view redraw.

        Args:
            evt: EditorEvent with updated tuning list.
        """
        tedit : TrackEditorView | None = self.track_editor_view
        if evt.tuning and self.track_model and tedit:
            self.track_model.tuning = evt.tuning 
            tedit.update()
 
    def measure_clicked(self, evt: EditorEvent):
        """Handle mouse click events selecting a measure in the track editor."""
        pass

    def string_bend_event(self, evt: EditorEvent):
        """Apply string bend pitch curves from dialog events to the active TabEvent.

        Args:
            evt: EditorEvent containing string bend curve parameters.
        """
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
        """Toggle the start-repeat barline flag on the current measure.

        Args:
            evt: EditorEvent instance.
        """
        tedit : TrackEditorView | None = self.track_editor_view
        if tedit:
            tedit.toggle_measure_start_repeat()
            
    def toggle_measure_end_repeat(self, evt: EditorEvent):
        """Toggle the end-repeat barline flag on the current measure.

        Args:
            evt: EditorEvent instance.
        """
        tedit : TrackEditorView | None = self.track_editor_view
        if tedit:
            tedit.toggle_measure_end_repeat()


    def propagate_undo_redo_model_change(self, track: Track):
        """Apply a restored track state from undo/redo history to the editor view.

        Args:
            track: The restored Track model.
        """
        assert(self.track_editor_view is not None)
        self.rup.disable_updates()
        self.track_model = track 
        self.track_editor_view.set_track_model(self.track_model)
        self.rup.enable_updates()
        self.track_editor_view.setFocus()

    def undo_event(self, evt: EditorEvent): 
        """Revert the track model to the previous state from history.

        Args:
            evt: EditorEvent instance.
        """
        new_model = self.rup.undo(self.track_model)
        if new_model:
            self.propagate_undo_redo_model_change(new_model)    

    def redo_event(self, evt: EditorEvent): 
        """Re-apply the next undone track state from history.

        Args:
            evt: EditorEvent instance.
        """
        new_model = self.rup.redo(self.track_model)
        if new_model:
            self.propagate_undo_redo_model_change(new_model)    

    def paste_event(self, evt: EditorEvent):
        """Paste TabEvents from the paste buffer into the active track.

        Args:
            evt: EditorEvent instance.
        """
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view
        if tmodel is not None and tedit is not None: 
            paste_buffer = PasteBufferSingleton()
            paste_buffer.paste(tmodel, tedit)
            tedit.model_updated()

    def cut_event(self, evt: EditorEvent):
        """Cut the selected TabEvents into the clipboard paste buffer.

        Args:
            evt: EditorEvent instance.
        """
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view
        if tmodel is not None and tedit is not None: 
            paste_buffer = PasteBufferSingleton()
            if paste_buffer.cut(tmodel, tedit):
                tedit.model_updated()

    def copy_event(self, evt: EditorEvent):
        """Copy the selected TabEvents into the clipboard paste buffer.

        Args:
            evt: EditorEvent instance.
        """
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view
        if tmodel is not None and tedit is not None: 
            paste_buffer = PasteBufferSingleton()
            if paste_buffer.copy(tmodel, tedit):
                tedit.model_updated()

    def on_rest_dur_changed(self, evt : EditorEvent):
        """Adjust adjacent rests when the rest duration changes to keep measure beat counts balanced.

        Args:
            evt: EditorEvent containing duration delta details.
        """
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view
        if tmodel is not None and tedit is not None: 
            te, m = tmodel.current_moment()
            i = m.tab_events.index(te)
            d = evt.dur_change # <new_duration> - te.duration

            if evt.new_dur == 0:
                return
            
            def _adjacent_rests() -> List[Tuple[int, TabEvent]]:
                """Find trailing consecutive rests with identical dotting properties."""
                r = []
                for n in range(i+1,len(m.tab_events)):
                    n_te = m.tab_events[n]
                    if not n_te.is_rest():
                        break
                    if n_te.dotted != te.dotted:
                        break
                    if n_te.double_dotted != te.double_dotted:
                        break
                    r.append((n,n_te))
                return r
            
            def _insert_rests():
                """Insert supplementary rests to fill the remaining duration gap."""
                c = math.fabs(evt.dur_change / evt.new_dur)
                if math.fmod(c, 1.0) != 0.0:
                    return
                insList = []
                for j in range(0,int(c)):
                    item = TabEvent(te.num_gstrings)
                    item.duration = evt.new_dur
                    insList.append( item )
                m.tab_events = m.tab_events[:i+1] + insList + m.tab_events[i+1:]
                tedit.model_updated() # type: ignore                

            if evt.dur_change < 0:
                _insert_rests()
            elif evt.dur_change > 0 and te.is_rest():
                sum_d = 0
                rem_list = []
                for n_te in m.tab_events[i+1:]:
                    sum_d += n_te.duration
                    rem_list.append(n_te)
                    if sum_d == evt.dur_change:
                        for n_te in rem_list:
                            m.tab_events.remove(n_te)    
                        tedit.model_updated() # type: ignore
                        break

            # evt.dur_changed = new_duration - te.duration
            pass

    def on_model_sync(self, evt : EditorEvent):
        """Notify the editor view to redraw following external model updates.

        Args:
            evt: EditorEvent instance.
        """
        if self.track_editor_view:
            self.track_editor_view.model_updated() 
            self.track_editor_view.setFocus()

    def on_focus(self, evt: EditorEvent):
        """Transfer keyboard focus back to the track editor view.

        Args:
            evt: EditorEvent instance.
        """
        if self.track_editor_view:
            self.track_editor_view.setFocus()

    def on_drumcode_select(self, evt: EditorEvent):
        """Assign selected MIDI drum key code to the active note position.

        Args:
            evt: EditorEvent containing midi_drum_code.
        """
        tmodel : Track | None = self.track_model
        tedit : TrackEditorView | None = self.track_editor_view
        if tmodel and tedit:
            te, _ = tmodel.current_moment()
            te.fret[te.string] = evt.midi_drum_code
            tedit.current_tab_event_updated()
            tedit.setFocus()

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
        EditorEvent.REDO_EVENT: redo_event,
        EditorEvent.PASTE_EVENT: paste_event,
        EditorEvent.CUT_EVENT: cut_event,
        EditorEvent.COPY_EVENT: copy_event,

        EditorEvent.REST_DUR_CHANGED: on_rest_dur_changed,
        EditorEvent.SYNC_MODEL_TO_VIEW: on_model_sync,
        EditorEvent.FOCUS: on_focus,
        EditorEvent.DRUM_DIALOG_SELECT: on_drumcode_select
    }

    def editor_event(self, evt: EditorEvent):
        """Route incoming EditorEvent to its registered handler in the dispatch dictionary.

        Args:
            evt: EditorEvent to dispatch.

        Raises:
            RuntimeError: If evt.ev_type has no registered handler.
        """
        func = self.dispatch.get(evt.ev_type)  # type: ignore
        if func:
            func(self, evt)  # type: ignore
        else:
            text = "Unsupported event type %d" % evt.ev_type
            logging.error(vars(evt))
            raise RuntimeError(text)

    def __init__(self):
        """Initialize EditorController with undo/redo manager, key processor, and event listeners."""
        self.rup = RedoUndoProcessor()
        self.keymap = EditorKeyMap()
        self.track_model = None
        self.track_editor_view = None
        # track model -> cursor
        self.key_proc = KeyProcessor()
        self.sequence_renderer = None
        
        Signals.editor_event.connect(self.editor_event)
        