from view.editor.measurePresenter import MeasurePresenter
from view.editor.tabEventPresenter import TabEventPresenter


from PyQt6.QtWidgets import (QWidget, QHBoxLayout)
from models.measure import Measure, TabEvent
from models.track import Track


class TrackPresenter(QWidget):

    def setup(self):
        "precalculate variables needed for operations"
        (self.current_tab_event, self.current_measure) = \
            self.track_model.current_moment()
        self.current_mp : MeasurePresenter = \
            self.mp_map[self.current_measure]
        self.current_tep : TabEventPresenter = \
            self.current_mp.tab_map[self.current_tab_event]
        self.current_tep.cursor_on()

    def __init__(self, track_model: Track):
        super().__init__()
        self.measure_layout = QHBoxLayout(self)
        self.measure_layout.setSpacing(0)
        self.track_model = track_model
        self.mp_map = {}

        for measure in track_model.measures:
            mp = MeasurePresenter(measure, track_model)
            self.mp_map[measure] = mp 
            self.measure_layout.addWidget(mp)

        self.setup()

    def cursor_up(self):
        self.current_tep.cursor_up()

    def cursor_down(self):
        self.current_tep.cursor_down()

    def prev_moment(self):
        "switch cursor off on current tab, switch on previous"
        (prev_tab, _) = self.track_model.prev_moment()
        if prev_tab:
            self.current_tep.cursor_off()
            # update current_tp
            self.setup()
            # set the prev tab event presenter to show the cursor 
            self.current_tep.cursor_on()

    def update_tab(self, new_te: TabEvent):
        # update the tab event inside the current tab event presentor
        self.current_tab_event.update(new_te)
        
        # check to see if there is a beat over/under flow and 
        # show indicator in measure.
        self.current_mp.beat_error_check()
        self.update()


    def next_moment(self):
        """
        switch cursor off on current tab, switch on next

        If it does not exist then create a new
        blank measure and position cursor at the start of the 
        new measure.  
        """
        (next_tab, curr_measure) = self.track_model.next_moment()
        # are there still tabs?
        if next_tab:
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

            self.next_moment() # recursive call 


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

    te = TabEvent(6)
    te.duration = 2.0

    QTimer.singleShot(2000, lambda *args: window.update_tab(te) )

   
    window.show()
    sys.exit(app.exec())

