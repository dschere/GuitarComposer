""" 
Present a measure containing tab events.

Display staff notation such as the key, time signature, beats
per measure etc.

Also display an error indicator if there are too few or too 
many beats in the measure. 

"""
import copy

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,  QSpinBox)
from models.measure import Measure, TabEvent

from view.editor import glyphs
from view.editor.glyphs.common import ORNAMENT_MARKING_HEIGHT, STAFF_HEIGHT, STAFF_SYM_WIDTH
from view.editor.tabEventPresenter import TabEventPresenter 
from models.track import Track
from typing import Dict, List

from util.layoutGapWorkaround import adjust_size_to_fit


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

class RepeatMeasureBarlines(QWidget):
    SPIN_BOX_HEIGHT=24


    def update_repeat_count(self):
        value = int(self.spin_box.value())
        self.measure.repeat_count = value

    def __init__(self, measure: Measure, b_type : int):
        super().__init__()
        #self.setFixedWidth(STAFF_SYM_WIDTH)
        #self.setFixedHeight(ORNAMENT_MARKING_HEIGHT)

        self.measure = measure
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(1,100)
        self.spin_box.setValue(self.measure.repeat_count)
        self.spin_box.setToolTip("repeat count")
        self.spin_box.valueChanged.connect(self.update_repeat_count)
        self.spin_box.setFixedHeight(self.SPIN_BOX_HEIGHT)
        self.spin_box.setFixedWidth(STAFF_SYM_WIDTH)
 
        barlines = glyphs.StaffMeasureBarlines(
            measure.measure_number+1,
            b_type,
            STAFF_SYM_WIDTH,
            STAFF_HEIGHT - self.SPIN_BOX_HEIGHT
        )

        layout.addWidget(barlines)
        layout.addWidget(self.spin_box)
        self.setLayout(layout)



class MeasureLine(QWidget):

    def _create_measure_bar(self):
        use_rc_ctlr = False
        b_type = glyphs.StaffMeasureBarlines.END_MEASURE
        measure = self.measure

        if measure.start_repeat and measure.end_repeat:
            b_type = glyphs.StaffMeasureBarlines.END_BEGIN_NEW_REPEAT
            use_rc_ctlr = True
        elif measure.end_repeat:
            b_type = glyphs.StaffMeasureBarlines.END_REPEAT
            use_rc_ctlr = True
        elif measure.start_repeat:
            b_type = glyphs.StaffMeasureBarlines.BEGIN_REPEAT
        
        if use_rc_ctlr:
            measure_glyph = RepeatMeasureBarlines(measure, b_type)
        else:
            measure_glyph = \
                glyphs.StaffMeasureBarlines(
                    measure.measure_number+1,
                    b_type
                )
        return measure_glyph

    def __init__(self, measure: Measure, tm: Track, initial_measure = False):
        super().__init__()
        self.measure = measure

        layout = QVBoxLayout(self)
        layout.setSpacing(0) 
        layout.setContentsMargins(0, 0, 0, 0)

        tab_presentation = glyphs.TabletureMeasure()

        te = TabEvent(len(tm.tuning))
        ornamental_presentation = glyphs.oramental_markings(te)

        if initial_measure:
            # This is first meassure, the line type is start 
            # of staff 
            b_type = glyphs.StaffMeasureBarlines.START_OF_STAFF
            if measure.start_repeat:
                # the 1st measure is also a start of a repeat
                b_type = glyphs.StaffMeasureBarlines.BEGIN_REPEAT

            self.measure_glyph = glyphs.StaffMeasureBarlines(
                1, 
                b_type
            )
        else:
            self.measure_glyph = self._create_measure_bar()    
        
        layout.addWidget(self.measure_glyph)
        layout.addWidget(ornamental_presentation)
        layout.addWidget(tab_presentation)

        self.setLayout(layout)
        self.the_layout = layout 

    def update_bar_ctrl(self):
        layout = self.the_layout
        old_measure_glyph = layout.itemAt(0).widget()  # type: ignore
        new_measure_glyph = self._create_measure_bar()
        layout.removeWidget(old_measure_glyph)
        old_measure_glyph.deleteLater() # type: ignore
        layout.insertWidget(0, new_measure_glyph)               
 

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

    def reset_presentation(self):
        "purge all widgets in layout and rebuild presentation"
        while self.measure_layout.count() > 0:
            w = self.measure_layout.itemAt(0)
            assert(w)
            self.measure_layout.removeWidget(w.widget())
                 
        self.tab_map : Dict[TabEvent, TabEventPresenter] = {}
        
        self.create_staff_if_needed()
        # If start of staff draw a special measure line.
        if self.measure.measure_number == 1:
            start_track_measure_glyph = MeasureLine(
                self.measure, self.track_model, True)
            self.measure_layout.addWidget(start_track_measure_glyph)
            self.start_track_measure_glyph = start_track_measure_glyph
                         
        for tab_event in self.measure.tab_events:
            tp = TabEventPresenter(tab_event, self.measure, self.track_model)
            self.measure_layout.addWidget(tp)
            self.tab_map[tab_event] = tp

        self.measure_glyph = MeasureLine(self.measure, self.track_model, False)
        self.measure_layout.addWidget(self.measure_glyph)

        # test for beat errors
        self.beat_error_check()

        adjust_size_to_fit(self.measure_layout, self)
        self.update()

    def update_measure_line(self):
        if self.measure_glyph:
            self.measure_glyph.update_bar_ctrl()
            adjust_size_to_fit(self.measure_layout, self)
            self.update()


    def __init__(self, measure: Measure, track_model: Track):
        super().__init__()
        self.measure_layout = QHBoxLayout(self)
        self.measure_layout.setSpacing(0)
        self.measure_layout.setContentsMargins(0, 0, 0, 0)

        self.measure = measure
        self.track_model = track_model
        self.staff_header = None
        self.start_track_measure_glyph = None
        self.measure_glyph = None

        # associate a tab_presenter widget with
        # a TabEvent
        self.tab_map : Dict[TabEvent, TabEventPresenter] = {}

        self.create_staff_if_needed()
        # If start of staff draw a special measure line.
        if measure.measure_number == 1:
            start_track_measure_glyph = MeasureLine(
                measure, track_model, True)
            self.measure_layout.addWidget(start_track_measure_glyph)
                         
        for tab_event in self.measure.tab_events:
            tp = TabEventPresenter(tab_event, measure, track_model)
            self.measure_layout.addWidget(tp)
            self.tab_map[tab_event] = tp


        self.measure_glyph = MeasureLine(measure, track_model, False)
        self.measure_layout.addWidget(self.measure_glyph)

        adjust_size_to_fit(self.measure_layout, self)

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


