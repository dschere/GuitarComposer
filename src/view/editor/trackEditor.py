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
from PyQt6.QtWidgets import (QWidget, QGridLayout, 
                             QSizePolicy, QVBoxLayout, 
                             QToolBar, QButtonGroup, QPushButton)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

from view.editor.glyphs.staff import StaffGlyph
from view.events import Signals, EditorEvent
from view.config import EditorKeyMap

from view.editor import glyphs
from models.track import StaffEvent, TabCursor, Track
from view.editor.toolbar import EditorToolbar
from pkg_resources._vendor.more_itertools.more import stagger


        

class TrackEditor(QWidget):
    """ 
    Controls editing of the selected track in the navigator.
    """
    STAFF_ROW = 0
    TAB_ROW = 1
    EFFECTS_ROW = 2

    """
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:  # Check for left mouse button
            x = event.position().x()
            y = event.position().y()
            print(f"Mouse clicked at: x={x}, y={y}")
    """
            
    def setHeader(self, se : StaffEvent, col = 0):
        symbol = se.cleff
        row = self.STAFF_ROW
        # todo, determine symbol based on instrument assigned to track.
        g = glyphs.StaffHeaderGlyph(symbol,se.key,se.signature,se.bpm)
        self._grid_layout.addWidget(g, row, col)

    def setBlankSelectRegion(self, tc: TabCursor, col=1, gstring=5):
        """ 
        Sets up an empty region for editing a code/note/rest which includes
        both tablature and staff.
        """
        staff = glyphs.StaffGlyph(tc)
        tab = glyphs.TabletureGlyph()
        self._grid_add(staff, self.STAFF_ROW, col)
        self._grid_add(tab, self.TAB_ROW, col)
        tab.set_cursor(gstring)

    def setSelectRegion(self, col : int , gstring : int):
        """ 
        Move editing region on tableture, do auto scrolling if nessessary if
        edit region is no longer visible.
        """
        tab = self._grid_get(self.TAB_ROW, col)
        if tab:
            tab.set_cursor(gstring)

    def setFretValue(self, col : int, gstring : int, fret : int):
        tab = self._grid_get(self.TAB_ROW, col)
        if tab:
            tab.set_tab_note(gstring, fret)

    def renderStaffEngraving(self, se: StaffEvent, tmodel: Track, col: int):
        """ 
        Performs the work of rendering music notation based on tableture
        information. The controller will generatr Note|Chord events based
        on fret information.
        """
        staff_glyph = self._grid_get(self.STAFF_ROW, col)
        if staff_glyph and isinstance(staff_glyph, StaffGlyph):
            staff_glyph.setup(se, tmodel.getTabCursor(), tmodel.tuning)

    def setToolbar(self, tc: TabCursor):
        self.toolbar.setTabCursor(tc)

    def _grid_add(self, w, row, col):
        self._grid_layout.addWidget(w, row, col, alignment=Qt.AlignmentFlag.AlignLeft)
        self._widget_grid[(row,col)] = w

    def _grid_get(self, row, col):
        return self._widget_grid.get((row,col))
             
    def update_track_editor_content(self):
        # force an update of the canvas
        self.canvas.update()
        self.canvas.setFocus()

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        # main layout for toolbar and scrolling area 
        main_layout = QVBoxLayout(self)

        self.canvas = QWidget() 
        self.toolbar = EditorToolbar(TabCursor(6), self.update_track_editor_content)
         
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas) 

        #self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._grid_layout = QGridLayout()
        self._grid_layout.setHorizontalSpacing(0)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        self._widget_grid = {}

        self.canvas.setLayout(self._grid_layout)

        self.setLayout(main_layout)

        # signal controller
        evt = EditorEvent()
        evt.ev_type = EditorEvent.ADD_TRACK_EDITOR
        evt.track_editor = self
        Signals.editor_event.emit(evt)
