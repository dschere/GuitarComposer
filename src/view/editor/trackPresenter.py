import copy, logging
import uuid

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QScrollArea)
from PyQt6.QtCore import Qt, QPointF

from view.editor.measurePresenter import MeasurePresenter
from view.editor.tabEventPresenter import TabEventPresenter


from models.measure import Measure, TabEvent
from models.track import Track


from view.events import PlayerVisualEvent, Signals
from view.editor.pastebuffer import PasteBufferSingleton
from .overlay import OverlayWidget

         

class TrackPresenter(QWidget):
        

    def setup(self):
        if self.track_model is None: return 

        "precalculate variables needed for operations"
        (self.current_tab_event, self.current_measure) = \
            self.track_model.current_moment()
        self.current_mp : MeasurePresenter = \
            self.mp_map[self.current_measure]
        # carry over the value of the gstring which determines 
        # where the cursor is drawn 
        prior_string = None 
        if self.current_tep:
            prior_string = self.current_tep.get_string() 
        self.current_tep = self.current_mp.tab_map[self.current_tab_event]
        if prior_string is not None:
            self.current_tep.set_string(prior_string)
        self.current_tep.cursor_on()
        self.current_tep.update() 

        width = 100
        for measure in self.track_model.measures:
            mp = self.mp_map[measure]
            width += int(mp.width())
        self.setMinimumWidth(width)

        # draw tied notes etc.
        self.overlay.setup(self.track_model, self.mp_map)

        Signals.redo_undo_update.emit(self.track_model)

    def update_measure_repeat(self, m: Measure):
        "update the measure line for at the end of measure"
        tp : MeasurePresenter | None = self.mp_map.get(m)
        if tp:
            tp.update_measure_line()


    def current_tab_event_updated(self):
        self.setup()
        self.current_mp.beat_error_check()

    def set_fret(self, n : int):
        if self.current_tep is not None:
            self.current_tep.set_fret(n)
        self.setup() 

    def set_duration(self, d: float):
        self.current_tab_event.duration = d
        self.setup() 

    def set_dotted(self, state: bool):
        self.current_tab_event.dotted = state
        self.current_tab_event.double_dotted = not state
        self.setup() 
        
    def set_double_dotted(self, state: bool):
        self.current_tab_event.dotted = not state
        self.current_tab_event.double_dotted = state
        self.setup()

    def set_articulation(self, articulation):
        """ 
        Apply staccato, legato or none to the current momement and all subsiquent
        momements unless unless if there is a change 
        """

    def set_dynamic(self, dynamic):
        """
        Apply the dynamic to current momemnt and all subsiquent moments until a different
        dynamic encountered. 
        """    

    def insert_tab_copy(self):
        # create a copy of the current tab and insert
        # a neew tab event after the current one in the measure.
        new_tab = copy.deepcopy(self.current_tab_event)
        new_tab.uuid = str(uuid.uuid4())
        
        self.current_measure.insert_after_current(new_tab)
        #self.current_measure.tab_events
        self.current_mp.reset_presentation()
        self.setup()

    def delete_current_measure(self):
        "Delete current measure unless its the first measure, then ignore"
        # remove view
        if self.current_measure.measure_number != 1:
            self.measure_layout.removeWidget(self.current_mp)
            del self.mp_map[self.current_measure]  
            self.track_model.remove_measure()
            for mp in self.mp_map.values():
                mp.reset_presentation()

    def delete_tab(self):
        if len(self.current_measure.tab_events) == 1:
            # delete measure
            self.delete_current_measure()
        else:
            self.current_measure.remove_current()
            self.current_mp.reset_presentation()
        self.setup()

    def tab_event_changed(self):
        self.current_mp.reset_presentation()
        self.setup()

    def __init__(self, track_model: Track):
        super().__init__()
        #self.setWidgetResizable(True)
        self.measure_layout = QHBoxLayout(self)
        self.measure_layout.setSpacing(0)
        self.measure_layout.setContentsMargins(0, 0, 0, 0)
        self.measure_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.current_tep : TabEventPresenter | None = None
        self.track_model = track_model
        self.mp_map = {}

        for measure in track_model.measures:
            mp = MeasurePresenter(measure, track_model)
            self.mp_map[measure] = mp 
            self.measure_layout.addWidget(mp)

        # for drawing on top of staff
        self.overlay = OverlayWidget(self)

        Signals.player_visual_event.connect(self.play_visual_event)        
        self.setup()

    def play_visual_event(self, evt : PlayerVisualEvent):
        tab_event = evt.tab_event 
        # get the measure presenter for this tab event
        m = self.track_model.find_tab_measure(tab_event)
        if m:
            # get the tab event presenter associated with the
            # tab_event
            mp = self.mp_map.get(m)
            if not mp:
                return
            tp : TabEventPresenter | None = None # mp.tab_map.get(tab_event)
            for te in mp.tab_map:
                if te.uuid == tab_event.uuid:
                    tp = mp.tab_map.get(te)
                    break

            # switch playing highlight on/off
            if not tp:
                pass
            elif evt.ev_type == evt.TABEVENT_HIGHLIGHT_ON:
                #logging.info("set_play_line tp id %ld" % id(tp))
                tp.set_play_line()
            elif evt.ev_type == evt.TABEVENT_HIGHLIGHT_OFF:
                #logging.info("clear_play_line tp id %ld" % id(tp))
                tp.clear_play_line()
            

    def cursor_up(self):
        if self.current_tep:
            self.current_tep.cursor_up()

    def cursor_down(self):
        if self.current_tep:
            self.current_tep.cursor_down()

    def prev_moment(self, ctrl_pressed = False):
        "switch cursor off on current tab, switch on previous"
        paste_buffer = PasteBufferSingleton()

        (prev_tab, _) = self.track_model.prev_moment()
        if prev_tab and self.current_tep is not None:
            self.current_tep.cursor_off()
            # update current_tp
            self.setup()
            # set the prev tab event presenter to show the cursor 
            self.current_tep.cursor_on()
            if ctrl_pressed:
                self.current_tep.set_copy_highlight()
                paste_buffer.append(self.current_tep)
            

    def update_tab(self, new_te: TabEvent):
        # update the tab event inside the current tab event presentor
        self.current_tab_event.update(new_te)
        
        # check to see if there is a beat over/under flow and 
        # show indicator in measure.
        self.current_mp.beat_error_check()
        self.update()

    def next_moment(self, ctrl_pressed = False):
        """
        switch cursor off on current tab, switch on next

        If it does not exist then create a new
        blank measure and position cursor at the start of the 
        new measure.  
        """
        paste_buffer = PasteBufferSingleton()

        (next_tab, curr_measure) = self.track_model.next_moment()
        # are there still tabs?
        if next_tab and self.current_tep is not None:
            self.current_tep.cursor_off()
            # update current_tp
            self.setup()
            # set the next tab event presenter to show the cursor 
            self.current_tep.cursor_on()
            if ctrl_pressed:
                self.current_tep.set_copy_highlight()
                paste_buffer.append(self.current_tep)
                
        else:
            # we reached the end we need to create a new measure
            # and position the cursor at the start of the measure.
            n = curr_measure.measure_number + 1
            # create new measure and append to model
            measure = self.track_model.append_measure(measure_number=n)

            # create a presenter for the measure
            mp = MeasurePresenter(measure, self.track_model)
            # add reference
            self.mp_map[measure] = mp
            # add to layout
            self.measure_layout.addWidget(mp)

            self.next_moment(ctrl_pressed) # recursive call 


if __name__ == '__main__':
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
    window = TrackPresenter(t)
    
    QTimer.singleShot(100, lambda *args: window.cursor_up())
    QTimer.singleShot(200, lambda *args: window.cursor_up())
    QTimer.singleShot(300, lambda *args: window.cursor_up())
    QTimer.singleShot(400, lambda *args: window.cursor_up())
    QTimer.singleShot(500, lambda *args: window.cursor_up())
    QTimer.singleShot(600, lambda *args: window.cursor_up())

    QTimer.singleShot(700, lambda *args: window.next_moment())
    QTimer.singleShot(800, lambda *args: window.next_moment())
    QTimer.singleShot(900, lambda *args: window.next_moment())
    QTimer.singleShot(1000, lambda *args: window.next_moment())
    QTimer.singleShot(1100, lambda *args: window.next_moment())

    QTimer.singleShot(1200, lambda *args: window.prev_moment())
    QTimer.singleShot(1300, lambda *args: window.prev_moment())
    QTimer.singleShot(1400, lambda *args: window.prev_moment())
    QTimer.singleShot(1500, lambda *args: window.prev_moment())
    QTimer.singleShot(1600, lambda *args: window.prev_moment())

    QTimer.singleShot(1800, lambda *args: window.insert_tab_copy())

    QTimer.singleShot(2100, lambda *args: window.delete_tab())
    
    # te = TabEvent(6)
    # te.duration = 2.0

    def test(*args):

        te, m = t.current_moment()
        te.duration = 2.0
        window.tab_event_changed()

    QTimer.singleShot(2300, test)

    # QTimer.singleShot(2000, lambda *args: window.update_tab(te) )

   
    window.show()
    sys.exit(app.exec())

