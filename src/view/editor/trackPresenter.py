import copy, logging
from typing import List
import uuid

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QScrollArea)
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

from view.editor.measurePresenter import MeasurePresenter
from view.editor.tabEventPresenter import TabEventPresenter


from models.measure import Measure, TabEvent
from models.track import Track


from view.events import MouseSelTab, PlayerVisualEvent, Signals
from view.editor.pastebuffer import PasteBufferSingleton
from .overlay import OverlayWidget

         

class TrackPresenter(QWidget):
    current_measure_changed = pyqtSignal(int)        

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

        self.current_measure_changed.emit(self.current_measure.measure_number-1)
        

        width = 100
        for measure in self.track_model.measures:
            mp = self.mp_map[measure]
            width += int(mp.width())
        self.setMinimumWidth(width)

        # draw tied notes etc.
        self.overlay.setup(self.track_model, self.mp_map)

        Signals.redo_undo_update.emit(self.track_model)


        # if self.prev_measure != -1:
        #     if self.prev_measure != self.track_model.current_measure:
        #         self.current_measure_changed.emit(self.track_model.current_measure) 
        # self.prev_measure = self.track_model.current_measure

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

    def insert_tab_copy(self, te : TabEvent | None = None):
        # create a copy of the current tab and insert
        # a neew tab event after the current one in the measure.
        if te is None:
            new_tab = copy.deepcopy(self.current_tab_event)
        else:
            new_tab = copy.deepcopy(te)
        new_tab.uuid = str(uuid.uuid4())
        
        self.current_measure.insert_after_current(new_tab)
        #self.current_measure.tab_events
        self.current_mp.reset_presentation()
        self.setup()

    def insert_tab_events(self, teList : List[TabEvent]):
        for te in teList:
            self.insert_tab_copy(te)

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
        "Delete current tab event"

        # First we have to handle tuplets which if you delete one the tuplet must 
        # revert back to a non tuplet so a triplet eigth notes if you remove one become
        # two eight notes. 
        self.track_model.disable_tuplet_group_if_needed()

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

    def on_tab_select(self, evt: MouseSelTab):
        te = evt.tab
        for (midx,m) in enumerate(self.track_model.measures):
            if te in m.tab_events and self.current_tep is not None:
                mp = self.mp_map[m]
                #te_pres = mp.tab_map[te]

                # set current moment in track
                self.track_model.current_measure = midx
                m.current_tab_event = m.tab_events.index(te)

                # setup presents to show cursor at that position
                self.current_tep.cursor_off()
                te.string = evt.gstring
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
        Signals.tab_select.connect(self.on_tab_select)       
        self.setup()

    def _clear_layout(self):
        layout = self.measure_layout
        while layout.count():
            item = layout.takeAt(0)   # remove from layout
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)  


    def model_updated(self):
        self._clear_layout()

        # update measure presenters
        self.mp_map = {}
        for measure in self.track_model.measures:
            mp = MeasurePresenter(measure, self.track_model)
            self.mp_map[measure] = mp 
            self.measure_layout.addWidget(mp)

        # update overlat size
        self.overlay.resize(self.size())

        self.setup()

    def resizeEvent(self, event):
        self.overlay.resize(self.size())    
        super().resizeEvent(event)

    def play_visual_event(self, evt : PlayerVisualEvent):
        if evt.ev_type == evt.CLEAR_ALL:
            for measure in self.track_model.measures:
                mp = self.mp_map[measure]
                for tp in mp.tab_map.values(): 
                    if isinstance(tp, TabEventPresenter):
                        tp.clear_play_line()
            return

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
                self.overlay.setup(self.track_model, self.mp_map)
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
        if ctrl_pressed and isinstance(self.current_tep,TabEventPresenter):
            self.current_tep.set_copy_highlight()
            paste_buffer.append(self.current_tep)
        

        (next_tab, curr_measure) = self.track_model.next_moment()
        # are there still tabs?
        if next_tab and self.current_tep is not None:
            self.current_tep.cursor_off()
            # update current_tp
            self.setup()
            # set the next tab event presenter to show the cursor 
            self.current_tep.cursor_on()
                
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

