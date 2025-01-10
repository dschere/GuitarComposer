""" 
Present a measure containing tab events.

Display staff notation such as the key, time signature, beats
per measure etc.

Also display an error indicator if there are too few or too 
many beats in the measure. 

"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout)
from models.measure import Measure, TabEvent

from view.editor import glyphs
from view.editor.tabEventPresenter import TabEventPresenter 
from models.track import Track
from typing import Dict, List


class StaffHeader(QWidget):
    def __init__(self, tm : Track, *args):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        te : TabEvent = TabEvent(len(tm.tuning)) 
        self.staff_header = glyphs.StaffHeaderGlyph(*args)
        layout.addWidget(self.staff_header)

        ornamental_presentation = glyphs.oramental_markings(te)
        layout.addWidget(ornamental_presentation)

        tab_presentation        = glyphs.TabletureHeader()
        layout.addWidget(tab_presentation)
        self.setLayout(layout)

class MeasureLine(QWidget):
    def __init__(self, measure: Measure, tm: Track, initial_measure = False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(0) 
        layout.setContentsMargins(0, 0, 0, 0)
    
        if initial_measure:
            # This is first meassure, the line type is start 
            # of staff 
            b_type = glyphs.StaffMeasureBarlines.START_OF_STAFF
            if measure.start_repeat:
                # the 1st measure is also a start of a repeat
                b_type = glyphs.StaffMeasureBarlines.BEGIN_REPEAT

            self.measure_glyph = glyphs.StaffMeasureBarlines(
                1, 
                b_type,
                -1
            )
        else:
            b_type = glyphs.StaffMeasureBarlines.END_MEASURE
            if measure.start_repeat and measure.end_repeat:
                b_type = glyphs.StaffMeasureBarlines.END_BEGIN_NEW_REPEAT
            elif measure.end_repeat:
                b_type = glyphs.StaffMeasureBarlines.END_REPEAT
            elif measure.start_repeat:
                b_type = glyphs.StaffMeasureBarlines.BEGIN_REPEAT
            
            self.measure_glyph = \
                glyphs.StaffMeasureBarlines(
                    measure.measure_number+1,
                    b_type,
                    measure.repeat_count
                )
        
        te = TabEvent(len(tm.tuning))
        
        layout.addWidget(self.measure_glyph)
        ornamental_presentation = glyphs.oramental_markings(te)
        layout.addWidget(ornamental_presentation)

        tab_presentation        = glyphs.TabletureMeasure()
        layout.addWidget(tab_presentation)
        self.setLayout(layout)


class MeasurePresenter(QWidget):

    def create_staff_if_needed(self):
        # Are there staff changes in this measure?
        if self.measure.staff_changes:
            self.staff_header = StaffHeader(self.track_model,
                self.measure.cleff,
                self.measure.key,
                self.measure.timesig,
                self.measure.bpm
            )
            self.measure_layout.addWidget(self.staff_header)

    def beat_overflow_error(self):
        for _tep in self.tab_map.values():
            tep : TabEventPresenter = _tep 
            tep.beat_overflow_error()
            
    def beat_underflow_error(self):
        for _tep in self.tab_map.values():
            tep : TabEventPresenter = _tep 
            tep.beat_underflow_error()
            
    def clear_beat_error(self):
        for _tep in self.tab_map.values():
            tep : TabEventPresenter = _tep 
            tep.clear_beat_error()

    def beat_error_check(self):
        (ts, _, _, _) = self.track_model.getMeasureParams(self.measure)
        teList : List[TabEvent] = list(self.tab_map.keys())
        
        beats = 0.0
        for te in teList:
            dur = ts.beat_duration()
            beats += te.beats(dur) 
        if beats > ts.beats_per_measure:
            self.beat_overflow_error() 
        elif beats < ts.beats_per_measure:
            self.beat_underflow_error()
        else:
            self.clear_beat_error()

    def __init__(self, measure: Measure, track_model: Track):
        super().__init__()
        self.measure_layout = QHBoxLayout(self)
        self.measure_layout.setSpacing(0)
        self.measure_layout.setContentsMargins(0, 0, 0, 0)

        self.measure = measure
        self.track_model = track_model
        # associate a tab_presenter widget with
        # a TabEvent
        self.tab_map : Dict[TabEvent, TabEventPresenter] = {}

        self.create_staff_if_needed()
        # If start of staff draw a special measure line.
        if measure.measure_number == 1:
            start_track_measure_glyph = MeasureLine(
                measure, track_model, True)
            self.measure_layout.addWidget(start_track_measure_glyph)
                
        prev : TabEventPresenter | None = None
        for tab_event in self.measure.tab_events:
            tp = TabEventPresenter(tab_event, measure, track_model)
            self.measure_layout.addWidget(tp)

            self.tab_map[tab_event] = tp

            # setup a linked list to make navigation easier.
            tp.prev = prev
            if prev:
                prev.next = tp
            prev = tp

        self.end_measure_glyph = MeasureLine(measure, track_model, False)
        self.measure_layout.addWidget(self.end_measure_glyph)

if __name__ == '__main__':
    from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTabWidget,
    QWidget, QSplitter, QStatusBar, QVBoxLayout, 
    QMenuBar, QMenu
    )
    import qdarktheme
    
    t = Track() 
    (te, measure) = t.current_moment()
    assert(te)

    import sys
    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    measure.key = "D"
    window = MeasurePresenter(measure, t)
    window.beat_underflow_error()
   
    window.show()
    sys.exit(app.exec())


