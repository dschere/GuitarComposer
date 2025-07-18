from PyQt6.QtWidgets import (QWidget, QGridLayout, 
                              QSizePolicy, QVBoxLayout, 
                              QToolBar, QButtonGroup, QPushButton, QScrollArea)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
from PyQt6 import QtCore

from models.measure import TabEvent
from view.editor.trackPresenter import TrackPresenter
from view.editor.toolbar import EditorToolbar
from models.track import Track
from view.events import EditorEvent, Signals, PlayerVisualEvent

from singleton_decorator import singleton 

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
        
    """ 
    API for the editorcontroller
    
    """    

    def set_track_model(self, track_model: Track):
        (tab_event, _) = track_model.current_moment()
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
        self.track_model = track_model

        # make this model accessible 
        TrackEditorData().set_active_track_model(track_model)

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
            

    def arrow_left_key(self):
        "-> move cursor to next moment, append to track if its the end."
        self.track_presenter.prev_moment()
        self.update_toolbar_track_event()

    def arrow_right_key(self):
        "<- move cursor to prev moment"
        self.track_presenter.next_moment()
        self.update_toolbar_track_event()

    def arrow_up_key(self):
        "^ move cursor up or loop if its the top fret"
        self.track_presenter.cursor_up()

    def arrow_down_key(self):
        "\/ move cursor down or loop if its the bottom fret"
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




""" 
Uses a grid layout widget to represent multiple tracks 

For non audio tracks 
Three rows are used to represent a instrument.
    staff
    tableture
    effects

Music glyphs are QLabels with pixmaps, using the QPaint 
to render images.    
    
operations:    
    Cut and Paste are implemented by keeping track of select grid elements
    arrow keys control column/row navigation along with mouse
    a green border rectangle indicates what is selected.

    to make notes line up a music symbol can use multiple columns.
    consider:
        track 1:  quater note          (3 cells with the middle one 
                                        used the others blank)
       

from PyQt6.QtWidgets import QLabel, QApplication, QMainWindow, QGridLayout, QWidget

import glyphs



def unittest():
    import sys
    app = QApplication(sys.argv)

    # layout = QGridLayout()

    # c = Canvas(40,200)
    # c.setGeometry(0, 0, 40, 120)

    # c.draw_staff_background()
    # c.show()


    layout = QGridLayout()
    layout.setHorizontalSpacing(0)

    layout.addWidget(glyphs.StaffHeaderGlyph(glyphs.TREBLE_CLEFF,"Eb","4/4",120), 0, 0)
    layout.addWidget(glyphs.StaffGlyph(), 0, 1)

    t = glyphs.TabletureGlyph()
    layout.addWidget(t, 1, 1)

    layout.addWidget(glyphs.EffectsGlyph(True), 2, 1)

    #t.setCursor(1, 13)
    t.set_cursor(1)
    #t.set_tab_note(1, 13)
    t.set_tab_note(2, 12)

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()




"""
# from PyQt6.QtWidgets import (QWidget, QGridLayout, 
#                              QSizePolicy, QVBoxLayout, 
#                              QToolBar, QButtonGroup, QPushButton, QScrollArea)
# from PyQt6.QtGui import QKeyEvent
# from PyQt6.QtCore import Qt

# from view.editor.glyphs.canvas import Canvas
# from view.editor.glyphs.staff import StaffGlyph
# from view.events import Signals, EditorEvent
# from view.config import EditorKeyMap

# from view.editor import glyphs
# from models.track import MeasureEvent, StaffEvent, TabEvent, Track
# from view.editor.toolbar import EditorToolbar
# #from pkg_resources._vendor.more_itertools.more import stagger
# from view.editor.glyphs.ornamental_markings import oramental_markings
# from typing import List
# from src.view.editor.glyphs.tableture import TabletureGlyph




# class TrackEditor(QWidget):
#     """ 
#     Controls editing of the selected track in the navigator.
#     """
#     STAFF_ROW = 0
#     ORAMENTS_ROW = 1
#     TAB_ROW = 2
#     EFFECTS_ROW = 3

#     """
#     def mousePressEvent(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:  # Check for left mouse button
#             x = event.position().x()
#             y = event.position().y()
#             print(f"Mouse clicked at: x={x}, y={y}")
#     """

#     def drawFirstMeasure(self, measure =1, col = 1):
#         g = glyphs.StaffMeasureBarlines(measure,
#                 glyphs.StaffMeasureBarlines.START_OF_STAFF)
#         row = self.STAFF_ROW
#         self._grid_layout.addWidget(g, row, col)

#         tm = glyphs.TabletureMeasure()
#         self._grid_layout.addWidget(tm, self.TAB_ROW, col)

#     def drawMeasure(self, measure =1, col = 1):
#         g = glyphs.StaffMeasureBarlines(measure,
#                 glyphs.StaffMeasureBarlines.END_MEASURE)
#         row = self.STAFF_ROW
#         self._grid_layout.addWidget(g, row, col)

#         tm = glyphs.TabletureMeasure()
#         self._grid_layout.addWidget(tm, self.TAB_ROW, col)

#     def drawBeginRepeat(self, measure = 1, col = 1):
#         g = glyphs.StaffMeasureBarlines(measure,
#                 glyphs.StaffMeasureBarlines.BEGIN_REPEAT)
#         row = self.STAFF_ROW
#         self._grid_layout.addWidget(g, row, col)

#     def drawEndRepeat(self, measure = 1, col = 1, count = 1):
#         g = glyphs.StaffMeasureBarlines(measure,
#                 glyphs.StaffMeasureBarlines.END_REPEAT, 
#                 repeat_count=count)
#         row = self.STAFF_ROW
#         self._grid_layout.addWidget(g, row, col)


#     def drawHeader(self, se : StaffEvent, col = 0):
#         symbol = se.cleff
#         row = self.STAFF_ROW
#         # todo, determine symbol based on instrument assigned to track.
#         g = glyphs.StaffHeaderGlyph(symbol,se.key,se.signature,se.bpm)
#         self._grid_layout.addWidget(g, row, col)

#         th = glyphs.TabletureHeader()
#         self._grid_layout.addWidget(th, self.TAB_ROW, col)

#     def move_cursor(self, col : int):
#         self.clearCursor()
#         tab = self._grid_get(self.TAB_ROW,col)
#         assert(tab != None)
#         tab.set_cursor(5) # type: ignore
#         tab.update()
#         self._current_cursor_col = col
        
#     _current_cursor_col = -1
#     def drawBlankSelectRegion(self, tc: TabEvent, col=2, gstring=5):
#         """ 
#         Sets up an empty region for editing a code/note/rest which includes
#         both tablature and staff.
#         """
#         self.clearCursor()
#         staff = glyphs.StaffGlyph(tc)
#         orn = oramental_markings(tc)
#         tab = glyphs.TabletureGlyph()
#         self._grid_add(staff, self.STAFF_ROW, col)
#         self._grid_add(orn, self.ORAMENTS_ROW, col)
#         self._grid_add(tab, self.TAB_ROW, col)
#         tab.set_cursor(gstring)
#         self._current_cursor_col = col

#     def drawSelectRegion(self, col : int , gstring : int):
#         """ 
#         Move editing region on tableture, do auto scrolling if nessessary if
#         edit region is no longer visible.
#         """
#         self.clearCursor()
#         tab = self._grid_get(self.TAB_ROW, col)
#         if tab:
#             tab.set_cursor(gstring) # type: ignore
#             self._current_cursor_col = col

#     def clearCursor(self):
#         if self._current_cursor_col != -1:
#             col = self._current_cursor_col
#             tab = self._grid_get(self.TAB_ROW, col)
#             if tab:
#                 tab.clear_cursor() # type: ignore
                
    
#     def drawFretValue(self, col : int, gstring : int, fret : int):
#         tab = self._grid_get(self.TAB_ROW, col)
#         if tab:
#             tab.set_tab_note(gstring, fret) # type: ignore

#     def drawStaffEngraving(self, se: StaffEvent, te: TabEvent, col: int, tuning: List[str]):
#         """ 
#         Performs the work of rendering music notation based on tableture
#         information. The controller will generatr Note|Chord events based
#         on fret information.
#         """
#         staff_glyph = self._grid_get(self.STAFF_ROW, col)
#         if staff_glyph and isinstance(staff_glyph, StaffGlyph):
#             staff_glyph.setup(se, te, tuning)

#     def setToolbar(self, tc: TabEvent):
#         self.toolbar.setTabCursor(tc)

#     def _grid_add(self, w, row, col):
#         item = self._grid_layout.itemAtPosition(row, col)
#         if item:
#             self._grid_layout.removeItem(item)

#         self._grid_layout.addWidget(w, row, col, alignment=Qt.AlignmentFlag.AlignLeft)
#         #self._widget_grid[(row,col)] = w
        
#         # THIS IS A WORKAROUND
#         # The setSpacing is not working for the grid so I change the max width
#         # to computed width of all widgets.
#         num_cols = self._grid_layout.columnCount()
#         total_width = 0
#         for c in range(0,num_cols):
#             item = self._grid_layout.itemAtPosition(0, c)
#             if item:
#                 ww : QWidget | None = item.widget()
#                 if ww:
#                     total_width += ww.width()                     
#         self.canvas.setMaximumWidth(total_width)

#     def _grid_get(self, row, col):
#         item = self._grid_layout.itemAtPosition(row, col)
#         if item:
#             return item.widget()
#         #return self._widget_grid.get((row,col))
             
#     def update_track_editor_content(self):
#         # force a repaint of widgets canvas
#         self.canvas.update()
#         # set the focus of the cursor
#         self.canvas.setFocus()

#     def __init__(self):
#         super().__init__()
#         self.setSizePolicy(QSizePolicy.Policy.Expanding,
#                            QSizePolicy.Policy.Expanding)

#         # main layout for toolbar and scrolling area 
#         main_layout = QVBoxLayout(self)
        
#         scroll_area = QScrollArea()
#         scroll_area.setWidgetResizable(True) 
        
#         self.canvas = QWidget() 
#         self.toolbar = EditorToolbar(TabEvent(6), self.update_track_editor_content)
         
#         main_layout.addWidget(self.toolbar)
#         scroll_area.setWidget(self.canvas)

#         main_layout.addWidget(scroll_area) 

#         #self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
#         self._grid_layout = QGridLayout()
#         self._grid_layout.setHorizontalSpacing(0)
#         self._grid_layout.setContentsMargins(0, 0, 0, 0)
#         self._grid_layout.setSpacing(0)
        

#         self._widget_grid = {}

#         self.canvas.setLayout(self._grid_layout)

#         self.setLayout(main_layout)

#         # test adding 10 blank widgets
#         # print("test test test")
#         # for col in range(0,8,2):
#         #     se = StaffEvent() 
            
#         #     self.drawHeader(se, col)
#         #     self.drawMeasure(col, col+1) 
#         #     #te = TabEvent(6)
#         #     #self.drawBlankSelectRegion(te, col)  

#         # signal controller
#         evt = EditorEvent()
#         evt.ev_type = EditorEvent.ADD_TRACK_EDITOR
#         evt.track_editor = self # type: ignore
#         Signals.editor_event.emit(evt)
