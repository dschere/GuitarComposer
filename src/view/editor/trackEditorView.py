from PyQt6.QtWidgets import (QWidget, QGridLayout, 
                              QSizePolicy, QVBoxLayout, 
                              QToolBar, QButtonGroup, QPushButton, QScrollArea)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
from PyQt6 import QtCore

from PyQt6.QtCore import QObject, QEvent

from models.measure import TabEvent
from view.editor.trackPresenter import TrackPresenter
from view.editor.toolbar import EditorToolbar
from models.track import Track
from view.events import EditorEvent, Signals, PlayerVisualEvent

from singleton_decorator import singleton 
from .measureNavigation import MeasureNavigation
from view.config import EditorKeyMap

@singleton
class TrackEditorData:
    """ 
    All information about the current track being
    edited to be easilly available to glyphs.
    """
    def __init__(self):
        self.active_track_model = None

    def set_active_track_model(self, track: Track):
        self.active_track_model = track 

    def get_active_track_model(self) -> Track | None:
        return self.active_track_model

class BlockKeys(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down,
                               Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
                               Qt.Key.Key_Home, Qt.Key.Key_End):
                print("Blocked:", event.key())
                return True  # block
        return super().eventFilter(obj, event)

class TrackEditorView(QScrollArea):

    def _update_track_editor_content(self):
        # check for error
        if self.track_presenter.current_mp: 
            self.track_presenter.current_mp.beat_error_check()
        self.track_presenter.current_tab_event_updated()
        # force a repaint of widgets canvas
        self.track_presenter.update()
        # set the focus of the cursor
        self.track_presenter.setFocus()

        if hasattr(self,"track_model"):
            Signals.redo_undo_update.emit(self.track_model)


    def mnav_selected(self, midx):
        """
        Measure navigator, user has selected a new current measure 
        """
        if self.track_model is not None and self.track_presenter is not None:
            m = self.track_model.measures[midx]
            self.track_model.current_measure = midx
            m.current_tab_event = 0
            if self.track_presenter.current_tep is not None:
                self.track_presenter.current_tep.cursor_off()
            self.track_presenter.setup()

            mp = self.track_presenter.mp_map.get(m)
            self.scroll_area.ensureWidgetVisible(mp)

    def undoEdit(self):
        evt = EditorEvent(EditorEvent.UNDO_EVENT)
        Signals.editor_event.emit(evt)
        
    def redoEdit(self):
        evt = EditorEvent(EditorEvent.REDO_EVENT)
        Signals.editor_event.emit(evt)


    _ctrl_key_pressed = False
    _shift_key = False
    _arrow_keys = (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down)

    def keyReleaseEvent(self, event: QKeyEvent):
        editor_keymap = EditorKeyMap()
        key = event.key()
        mod = event.modifiers()
        
        if mod == Qt.KeyboardModifier.NoModifier:
            self._ctrl_key_pressed = False
        
        if Qt.Key.Key_Shift == key:
            self._shift_key = False
        # generate key event for right/left arrows on key release
        elif key in self._arrow_keys:
            e_evt = EditorEvent()
            e_evt.ev_type = EditorEvent.KEY_EVENT
            e_evt.key = key
            e_evt.control_key_pressed = self._ctrl_key_pressed
            Signals.editor_event.emit(e_evt) 
        
        elif mod & Qt.KeyboardModifier.ControlModifier:
            if key == editor_keymap.UNDO:
                self.undoEdit()
            elif key == editor_keymap.REDO:
                self.redoEdit()    

        return super().keyReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        editor_keymap = EditorKeyMap()
        e_evt = EditorEvent()


        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            e_evt.ev_type = EditorEvent.PASTE_EVENT
            Signals.editor_event.emit(e_evt)

        elif event.key() == Qt.Key.Key_X and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            e_evt.ev_type = EditorEvent.CUT_EVENT
            Signals.editor_event.emit(e_evt)

        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._ctrl_key_pressed = True
        elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
            pass
        else:
            key = event.key()
            if key in self._arrow_keys:
                pass
            elif key == Qt.Key.Key_Shift:
                self._shift_key = True
            else:
                if not self._shift_key and ord('Z') >= key >= ord('A'):     
                    key += 32 # make lower case

                e_evt.ev_type = EditorEvent.KEY_EVENT
                e_evt.key = key
                e_evt.control_key_pressed = self._ctrl_key_pressed
                Signals.editor_event.emit(e_evt)

        return super().keyPressEvent(event)



    """ 
    API for the editorcontroller
    
    """    

    def set_track_model(self, track_model: Track):
        (tab_event, _) = track_model.current_moment() # type: ignore
        # main layout for toolbar and scrolling area
            
        main_layout = self.layout()
        if main_layout:
            while main_layout.count():
                item = main_layout.takeAt(0)
                if widget := item.widget(): # type: ignore
                    widget.deleteLater()
        else:
            main_layout = QVBoxLayout(self)
            self.setLayout(main_layout)

        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # place holder track presenter until a track is 
        # selected.
        self.track_presenter = TrackPresenter(track_model)
        
        self.toolbar = EditorToolbar(track_model, self._update_track_editor_content)
         
        main_layout.addWidget(self.toolbar)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.track_presenter)
        scroll_area.setWidgetResizable(False)  # Important for custom-size canvas
        main_layout.addWidget(scroll_area)
        
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        w = scroll_area.viewport()
        if w:
            w.setFixedHeight(self.track_presenter.height())

        self.track_model = track_model

        mnav = MeasureNavigation(self, track_model)
        mnav.measure_change.connect(self.mnav_selected)

        # update navigation buttons when the current measure changes
        self.track_presenter.current_measure_changed.connect(mnav.set_measure)

        main_layout.addWidget(mnav)
        self.mnav = mnav 
        self.scroll_area = scroll_area

        # make this model accessible 
        TrackEditorData().set_active_track_model(track_model)

    def model_updated(self):
        self.track_presenter.model_updated()

    def get_track_model(self):
        return self.track_model

    def current_tab_event_updated(self):
        self.track_presenter.current_tab_event_updated()

    def update_toolbar_track_event(self):
        (te,_) = self.track_model.current_moment()
        self.toolbar.setTabEvent(te)

    def toggle_measure_start_repeat(self):
        # the start is really the end of the previos measure line
        m = self.track_model.get_measure()
        if m:
            if m.start_repeat:
                m.start_repeat = False 
            else:
                m.start_repeat = True 
            if m.measure_number == 1:
                mp = self.track_presenter.mp_map.get(m)
                if mp:
                    mp.update_start_measure_line()            
            else:
                p_m = self.track_model.get_measure(-1)    
                mp = self.track_presenter.mp_map.get(p_m)
                if mp:
                    mp.update_measure_line()

        #self.track_presenter.current_measure_updated()
 
    def toggle_measure_end_repeat(self):
        #(_,m) = self.track_model.current_moment()
        m = self.track_model.get_measure()
        if m:
            if m.end_repeat:
                m.end_repeat = False 
            else:
                m.end_repeat = True 
                if m.repeat_count == -1:
                    # set default
                    m.repeat_count = 2

            mp = self.track_presenter.mp_map.get(m)
            if mp:
                mp.update_measure_line()
            

    def arrow_left_key(self, ctrl_pressed: bool):
        "<- move cursor to next moment, append to track if its the end."
        self.track_presenter.prev_moment(ctrl_pressed)
        self.update_toolbar_track_event()

    def arrow_right_key(self, ctrl_pressed: bool):
        "-> move cursor to prev moment"
        prev_num_measures = len(self.track_model.measures)
        self.track_presenter.next_moment(ctrl_pressed)
        self.update_toolbar_track_event()

    def arrow_up_key(self):
        "^ move cursor up or loop if its the top fret"
        self.track_presenter.cursor_up()

    def arrow_down_key(self):
        "move cursor down or loop if its the bottom fret"
        self.track_presenter.cursor_down()

    def delete_key(self):
        self.track_presenter.delete_tab()
        self.update_toolbar_track_event()

    def insert_key(self):
        self.track_presenter.insert_tab_copy()
        self.update_toolbar_track_event() 

    def set_fret_value(self, n : int):
        self.track_presenter.set_fret(n)
        
    def set_duration(self, d: float):
        pass

    def set_dotted(self, state: bool):
        pass

    def set_double_dotted(self, state: bool):
        pass

    def start_copy(self):
        pass

    def end_copy(self):
        pass

    def paste(self, moment: int ):
        pass

    def cut(self):
        pass



    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        
        # signal controller
        evt = EditorEvent()
        evt.ev_type = EditorEvent.ADD_TRACK_EDITOR
        evt.track_editor = self # type: ignore
        Signals.editor_event.emit(evt)


def unittest():
    from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTabWidget,
    QWidget, QSplitter, QStatusBar, QVBoxLayout, 
    QMenuBar, QMenu
    )
    from PyQt6.QtCore import QTimer
    import qdarktheme
    
    t = Track() 
    (te, measure) = t.current_moment()
    assert(te)

    import sys
    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    measure.key = "E"
    window = TrackEditorView()

    window.set_track_model(t) 
   
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    unittest()


