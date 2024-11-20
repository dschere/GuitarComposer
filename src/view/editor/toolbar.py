"""
Track editor toolbars

<duration>
    whole -> sixtyforth note doted triplet quintuplet
<dynamic>
    ppp -> fff fadein fade out over long duration. 
<hand effects>
    bend / slide etc.
"""
from view.editor.glyphs.common import (
    WHOLE_NOTE,
    HALF_NOTE,
    QUATER_NOTE,
    EIGHT_NOTE,
    SIXTEENTH_NOTE,
    THRITYSEC_NOTE,
    SIXTYFORTH_NOTE,
    GHOST_NOTEHEAD,
    DOUBLE_GHOST_NOTEHEAD
    )
from PyQt6.QtWidgets import QToolBar, QWidget, QVBoxLayout, QPushButton,\
    QButtonGroup, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QObject

from music.constants import Dynamic
from models.track import TabCursor
from src.view.events import Signals

DOTTED = GHOST_NOTEHEAD
DOUBLE_DOTTED = DOUBLE_GHOST_NOTEHEAD
TRIPLET = "3"
QUINTIPLET = "5"
DURATION = "duration"
DYNAMIC = "dynamic"

class ToolbarButton(QPushButton):
    
    def __init__(self, parent, label, tooltip, p, v=None):
        super().__init__(label)
        self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setCheckable(True)
        self._param = p
        self._value = v
        self._parent = parent
        self.setFixedWidth(40)
   
    def pvalue(self):
        return self._value

    def pname(self):
        return self._param


# workaround for broken QButtonGroup
class MutuallyExclusiveButtonGroup(QObject):
    selected = pyqtSignal(ToolbarButton)

    def __init__(self):
        super().__init__()
        self.button_set = set()
        #TODO
        # create Signals.trackEditorToolbarKeyUpdate
        # connect to signal param,value if match then set click
        # search buttons in group to do this.call 'check_btn'
        # for param/value match

    def on_selected(self, clicked_btn):
        for btn in self.button_set:
            if btn is clicked_btn:
                self.selected.emit(clicked_btn)
            else:
                btn.setChecked(False)

    def check_btn(self, btn : ToolbarButton):
        btn.setChecked(True)
        self.on_selected(btn)

    def addButton(self, btn : ToolbarButton):
        self.button_set.add(btn)
        class selector:
            def __init__(self, p, btn):
                self.btn = btn
                self.p = p
            def __call__(self):
                self.p.on_selected(self.btn)
        btn.clicked.connect(selector(self, btn))



         

class EditorToolbar(QToolBar):

    def _compute_beat(self):
        n = 1.0

        if self._tab_cursor.dotted:
            n *= 1.5
        elif self._tab_cursor.double_dotted:
            n *= 1.75

        if self._tab_cursor.triplet:
            n *= 0.33
        elif self._tab_cursor.quintuplet:
            n *= 0.2

        self._tab_cursor.beat = n * self._tab_cursor.duration            
        

    def _dot_selected(self, btn: ToolbarButton):
        n = btn.pname()
        #TODO, move these strings to global constants
        if n == "clear-dots":
            self._tab_cursor.dotted = False 
            self._tab_cursor.double_dotted = False 
        elif n == "dotted":
            self._tab_cursor.dotted = True
            self._tab_cursor.double_dotted = False
        elif n == "double-dotted":
            self._tab_cursor.dotted = False
            self._tab_cursor.double_dotted = True
        self._compute_beat()

    def _on_duration_selected(self, btn: ToolbarButton):
        if btn.pname() == "duration":
            self._tab_cursor.duration = btn.pvalue() # type: ignore
        self._compute_beat() 

    def _dyn_selected(self, btn: ToolbarButton):
        if btn.pname() == "dynamic":
            self._tab_cursor.dynamic = btn.pvalue()


    def setTabCursor(self, tab_cursor : TabCursor):
        """
        set the tab cursor and react to any changes in data so 
        the toolbar reflects the state. 
        """ 
        self._tab_cursor = tab_cursor
        # select buttons based on tab settings

        # set the matching duration
        dlist = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625]
        if tab_cursor.duration in dlist:
            i = dlist.index(tab_cursor.duration)
            btn = self._dur_btns[i]
            self._dur_grp.check_btn(btn) 

        # set dot
        if tab_cursor.dotted:
            dotted_index = 1
            btn = self._dot_btns[dotted_index]        
            self._dot_grp.check_btn(btn) 
        elif tab_cursor.double_dotted:
            double_dotted_index = 2
            btn = self._dot_btns[double_dotted_index]        
            self._dot_grp.check_btn(btn) 
        else:
            no_dot_index = 0
            self._dot_grp.check_btn(self._dot_btns[no_dot_index])

        dyn_list = [Dynamic.FFF,Dynamic.FF,Dynamic.F,Dynamic.MF,
                    Dynamic.MP,Dynamic.P,Dynamic.PP,Dynamic.PPP]
        if tab_cursor.dynamic in dyn_list:
            i = dyn_list.index(tab_cursor.dynamic)
            btn = self._dyn_btns[i]
            self._dyn_grp.check_btn(btn)


    def __init__(self, tab_cursor : TabCursor):
        super().__init__()
        self._tab_cursor = tab_cursor
        self._lookup = {}
        self.setFixedHeight(30)

        # not duration whole -> 64th  
        self._dur_grp = MutuallyExclusiveButtonGroup()    
        self._dur_btns = (
            ToolbarButton(self, WHOLE_NOTE, "whole note", "duration", 4.0),
            ToolbarButton(self, HALF_NOTE, "half note", "duration", 2.0),
            ToolbarButton(self, QUATER_NOTE, "quarter note", "duration", 1.0),
            ToolbarButton(self, EIGHT_NOTE, "eight note", "duration", 0.5),
            ToolbarButton(self, SIXTEENTH_NOTE, "sixteenth note", "duration", 0.25),
            ToolbarButton(self, THRITYSEC_NOTE, "thirty second note", "duration", 0.125),
            ToolbarButton(self, SIXTYFORTH_NOTE, "sixty forth note", "duration", 0.0625)
        )
        for btn in self._dur_btns:
            self._dur_grp.addButton(btn)
            self.addWidget(btn)
        self._dur_grp.selected.connect(self._on_duration_selected)
        self.addSeparator()

        # dotted notes that alter standard note durations
        self._dot_grp = MutuallyExclusiveButtonGroup()
        self._dot_btns = (
            ToolbarButton(self, " ", "no dot", "clear-dots"),
            ToolbarButton(self, DOTTED, "dotted note", "dotted"),
            ToolbarButton(self, DOUBLE_DOTTED, "double dotted", "double-dotted")
        )
        for btn in self._dot_btns:
            self._dot_grp.addButton(btn)
            self.addWidget(btn)
        self._dot_grp.selected.connect(self._dot_selected) 
        self.addSeparator()

        # set dynamic
        self._dyn_grp = MutuallyExclusiveButtonGroup()
        self._dyn_btns = ( 
            ToolbarButton(self, "fff", Dynamic.tooltip(Dynamic.FFF), Dynamic.FFF),
            ToolbarButton(self, "ff", Dynamic.tooltip(Dynamic.FF), Dynamic.FF),
            ToolbarButton(self, "f", Dynamic.tooltip(Dynamic.F), Dynamic.F),
            ToolbarButton(self, "mf", Dynamic.tooltip(Dynamic.MF), Dynamic.MF),
            ToolbarButton(self, "mp", Dynamic.tooltip(Dynamic.MP), Dynamic.MP),
            ToolbarButton(self, "p", Dynamic.tooltip(Dynamic.P), Dynamic.P),
            ToolbarButton(self, "pp", Dynamic.tooltip(Dynamic.PP), Dynamic.PP),
            ToolbarButton(self, "ppp", Dynamic.tooltip(Dynamic.PPP), Dynamic.PPP)
        )
        for btn in self._dyn_btns:
            self._dyn_grp.addButton(btn) 
            self.addWidget(btn) 
        self._dyn_grp.selected.connect(self._dyn_selected)    

        self.setTabCursor(tab_cursor)





def unittest():
    import sys
    import qdarktheme

    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication([])

    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)


    mainwin = QMainWindow()

    tc = TabCursor(6)

    et = EditorToolbar(tc)
    mainwin.setCentralWidget(et)
    mainwin.show()

    sys.exit(app.exec())  # <- main event loop
if __name__ == '__main__':
    unittest()







