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
    DOUBLE_GHOST_NOTEHEAD,
    FORTE_SYMBOL,
    MEZZO_SYMBOL,
    PIANO_SYMBOL,
    STACCATO,
    LEGATO
    )
from PyQt6.QtWidgets import QToolBar, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor

from music.constants import Dynamic
from models.track import TabEvent

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

"""
class BendEffectToolbarButton(QPushButton):

    def __init__(self):
        super().__init__()
        self.setToolTip("Bend effect")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setCheckable(True)
        self.setFixedWidth(40)
   
    def paintEvent(self, event):
        # Call the base class paintEvent to ensure the button is drawn
        super().paintEvent(event)
        
        # Create a QPainter object
        painter = QPainter(self)
        
        # Set antialiasing for smoother curves
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define a Bézier curve using QPainterPath
        path = QPainterPath()
        width, height = self.width(), self.height()
        start_point = QPointF(0, height)
        control_point1 = QPointF(width / 3, height / 3)
        control_point2 = QPointF(2 * width / 3, 2 * height / 3)
        end_point = QPointF(width, 0)
        
        path.moveTo(start_point)
        path.cubicTo(control_point1, control_point2, end_point)
        
        # Set pen color and width
        pen = painter.pen()
        pen.setColor(QColor('cyan'))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the path
        painter.drawPath(path)    
"""    

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

    # def _compute_beat(self):
    #     n = 1.0

    #     if self._tab_event.dotted:
    #         n *= 1.5
    #     elif self._tab_event.double_dotted:
    #         n *= 1.75

    #     if self._tab_event.triplet:
    #         n *= 0.33
    #     elif self._tab_event.quintuplet:
    #         n *= 0.2

    #     self._tab_event.duration = n * self._tab_event.duration            
        

    def _dot_selected(self, btn: ToolbarButton):
        n = btn.pname()
        #TODO, move these strings to global constants
        if n == "clear-dots":
            self._tab_event.dotted = False 
            self._tab_event.double_dotted = False 
        elif n == "dotted":
            self._tab_event.dotted = True
            self._tab_event.double_dotted = False
        elif n == "double-dotted":
            self._tab_event.dotted = False
            self._tab_event.double_dotted = True
        else:
            # not a dot selected event.
            return    
        #self._compute_beat()
        self.update_staff_and_tab()

    def _on_duration_selected(self, btn: ToolbarButton):
        if btn.pname() == "duration":
            self._tab_event.note_duration = btn.pvalue() # type: ignore
            #self._compute_beat() 
        self.update_staff_and_tab()

    def _dyn_selected(self, btn: ToolbarButton):
        if btn.pname() == "dynamic":
            self._tab_event.dynamic = btn.pvalue()
        self.update_staff_and_tab()

    def _articulation_selected(self, btn: ToolbarButton):
        if btn.pname() == "clear-articulation":
            self._tab_event.legato = False
            self._tab_event.staccato = False
        elif btn.pname() == "legato":
            self._tab_event.legato = True
            self._tab_event.staccato = False
        elif btn.pname() == "staccato":
            self._tab_event.legato = False
            self._tab_event.staccato = True
        self.update_staff_and_tab()

    def _hand_effect_selected(self, btn: ToolbarButton):
        if btn.pname() == "clear-hand-effects":
            pass 
        elif btn.pname() == "bend-effect":
            pass


    def setTabEvent(self, tab_event : TabEvent):
        """
        set the tab cursor and react to any changes in data so 
        the toolbar reflects the state. 
        """ 
        self._tab_event = tab_event
        # select buttons based on tab settings

        # set the matching duration
        dlist = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625]
        if tab_event.duration in dlist:
            i = dlist.index(tab_event.duration)
            btn = self._dur_btns[i]
            self._dur_grp.check_btn(btn) 

        # set dot
        if tab_event.dotted:
            dotted_index = 1
            btn = self._dot_btns[dotted_index]        
            self._dot_grp.check_btn(btn) 
        elif tab_event.double_dotted:
            double_dotted_index = 2
            btn = self._dot_btns[double_dotted_index]        
            self._dot_grp.check_btn(btn) 
        else:
            no_dot_index = 0
            self._dot_grp.check_btn(self._dot_btns[no_dot_index])

        dyn_list = [Dynamic.FFF,Dynamic.FF,Dynamic.F,Dynamic.MF,
                    Dynamic.MP,Dynamic.P,Dynamic.PP,Dynamic.PPP]
        if tab_event.dynamic in dyn_list:
            i = dyn_list.index(tab_event.dynamic)
            btn = self._dyn_btns[i]
            self._dyn_grp.check_btn(btn)


    def __init__(self, tab_event: TabEvent, update_staff_and_tab):
        super().__init__()
        self._tab_event = tab_event 
                                         
        self._lookup = {}
        self.update_staff_and_tab = update_staff_and_tab
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
            ToolbarButton(self, DOUBLE_DOTTED, "double dotted", "double-dotted"),
            ToolbarButton(self, "3" + QUATER_NOTE, "triplet", "triplet"),
            ToolbarButton(self, "5" + QUATER_NOTE, "quintuplet", "quintuplet")
        )
        for btn in self._dot_btns:
            self._dot_grp.addButton(btn)
            self.addWidget(btn)
        self._dot_grp.selected.connect(self._dot_selected) 
        self.addSeparator()

        # set dynamic
        self._dyn_grp = MutuallyExclusiveButtonGroup()
        self._dyn_btns = ( 
            ToolbarButton(self, FORTE_SYMBOL * 3, Dynamic.tooltip(Dynamic.FFF), Dynamic.FFF),
            ToolbarButton(self, FORTE_SYMBOL * 2, Dynamic.tooltip(Dynamic.FF), Dynamic.FF),
            ToolbarButton(self, FORTE_SYMBOL, Dynamic.tooltip(Dynamic.F), Dynamic.F),
            ToolbarButton(self, MEZZO_SYMBOL + FORTE_SYMBOL, Dynamic.tooltip(Dynamic.MF), Dynamic.MF),
            ToolbarButton(self, MEZZO_SYMBOL + PIANO_SYMBOL, Dynamic.tooltip(Dynamic.MP), Dynamic.MP),
            ToolbarButton(self, PIANO_SYMBOL, Dynamic.tooltip(Dynamic.P), Dynamic.P),
            ToolbarButton(self, PIANO_SYMBOL * 2, Dynamic.tooltip(Dynamic.PP), Dynamic.PP),
            ToolbarButton(self, PIANO_SYMBOL * 3, Dynamic.tooltip(Dynamic.PPP), Dynamic.PPP)
        )
        for btn in self._dyn_btns:
            self._dyn_grp.addButton(btn) 
            self.addWidget(btn) 
        self._dyn_grp.selected.connect(self._dyn_selected)    
        self.addSeparator()

        
        self._articulation_group = MutuallyExclusiveButtonGroup()
        self._articulation_btns = (
            ToolbarButton(self, " ", "no articulation", "clear-articulation"),
            ToolbarButton(self, LEGATO, "legato", "legato"),
            ToolbarButton(self, STACCATO, "staccato", "staccato")
        )
        for btn in self._articulation_btns:
            self._articulation_group.addButton(btn) 
            self.addWidget(btn)
        self._articulation_group.selected.connect(self._articulation_selected)    
        
        self.setTabEvent(self._tab_event)
        self.addSeparator()

        self._hand_effects_group = MutuallyExclusiveButtonGroup() 
        self._hand_effects_btns = ( 
            ToolbarButton(self, " ", "no effects", "clear-hand-effects"),
            ToolbarButton(self, "bend", "bend", "bend-effect")
        )
        for btn in self._hand_effects_btns:
            self._hand_effects_group.addButton(btn) 
            self.addWidget(btn) 

       





