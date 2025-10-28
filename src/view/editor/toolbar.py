"""
Track editor toolbars

<duration>
    whole -> sixtyforth note doted triplet quintuplet
<dynamic>
    ppp -> fff fadein fade out over long duration. 
<hand effects>
    bend / slide etc.
"""
from view.dialogs.stringBendDialog import StringBendDialog
from view.editor.glyphs.common import (
    DOWNSTROKE,
    NO_ARTICULATION,
    UPSTROKE,
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
    LEGATO,
    TRIPLET_SYMBOL
    )
from PyQt6.QtWidgets import (QToolBar, QPushButton, 
    QSizePolicy, QWidget, QGroupBox, QHBoxLayout, QComboBox, QLabel)
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor

from music.constants import Dynamic
from models.track import TabEvent, Track
from view.events import StringBendEvent, EditorEvent, Signals
from models.measure import TupletTypes, TUPLET_DISABLED, TupletTypes


DOTTED = GHOST_NOTEHEAD
DOUBLE_DOTTED = DOUBLE_GHOST_NOTEHEAD
TRIPLET = "3"
QUINTIPLET = "5"
DURATION = "duration"
DYNAMIC = "dynamic"
StrokeDurationMap = {
    "all": 1.0,
    "3/4": 0.75,
    "2/3": 0.66,
    "1/2": 0.5,
    "1/3": 0.33,
    "1/4": 0.25,
    "1/8": 0.125
}
DefaultStrokeDuration = "1/2"
DefaultStrokeDurationIdx = 3

NO_STROKE_ID_VAL  = 0
UPSTROKE_ID_VAL   = 1
DOWNSTROKE_ID_VAL = -1




class ToolbarButton(QPushButton):
    
    def __init__(self, parent, label, tooltip, p, v=None):
        super().__init__(label)
        self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setCheckable(True)
        self._param = p
        self._value = v
        self._parent = parent
        self.setFixedSize(32,32)
        
        self.label = label
   
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

class ButtonGroupContainer(QWidget):
    def __init__(self, label):
        super().__init__()
        group_box = QGroupBox(label)
        group_box.setStyleSheet("""
            QGroupBox {
                padding: 0px;
                margin: 0px;
                border: 2px solid gray;
                border-radius: 5px; margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; padding: 0 3px;
            }
        """)
        self.item_layout = QHBoxLayout()
        group_box.setLayout(self.item_layout)

        group_layout = QHBoxLayout()
        group_layout.addWidget(group_box)
        self.setLayout(group_layout)

    def add_item(self, w):
        self.item_layout.addWidget(w)    
        



class EditorToolbar(QToolBar):


    def _dot_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()
        n = btn.pname()
        #TODO, move these strings to global constants
        if n == "clear-dots":
            te.dotted = False 
            te.double_dotted = False 
        elif n == "dotted":
            te.dotted = True
            te.double_dotted = False
        elif n == "double-dotted":
            te.dotted = False
            te.double_dotted = True
        elif n == "tied-note":
            te.tied_notes[te.string] = btn.isChecked()
        else:
            # not a dot selected event.
            return    
        #self._compute_beat()
        self.update_staff_and_tab()

    def _on_duration_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()
        if btn.pname() == "duration":
            te.duration = btn.pvalue() # type: ignore
            #self._compute_beat() 
        self.update_staff_and_tab()

    def _dyn_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()
        if btn.pname() == "dynamic":
            te.dynamic = btn.pvalue()
            te.render_dynamic = True
        self.update_staff_and_tab()

    def _on_stroke_direction_selected(self, *args):
        (te,_) = self.track_model.current_moment()
        t = self._stroke_duration.currentText()
        m = StrokeDurationMap.get(t)
        if m:
            # stroke duration in beats
            te.stroke_duration = te.duration * m
            te.stroke_duration_index = self._stroke_duration.currentIndex()

    def _on_stroke_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()
        if btn.pname() == "stroke":
            (te.upstroke,te.downstroke) = btn.pvalue()  # type: ignore
            self.update_staff_and_tab()


    def _articulation_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()

        if btn.pname() == "clear-articulation":
            te.legato = False
            te.staccato = False
            te.render_clear_articulation = True
        elif btn.pname() == "legato":
            te.legato = True
            te.staccato = False
        elif btn.pname() == "staccato":
            te.legato = False
            te.staccato = True
        self.update_staff_and_tab()

    def _hand_effect_selected(self, btn: ToolbarButton):
        (te,_) = self.track_model.current_moment()
        if btn.pname() == "clear-hand-effects":
            empty_evt = StringBendEvent()
            te.pitch_changes = empty_evt.pitch_changes 
            te.pitch_range = empty_evt.pitch_range
            
        elif btn.pname() == "bend-effect":
            # create dialog allow it to manipulate 'te'
            dialog = StringBendDialog(self)
            
            def on_apply(evt : StringBendEvent):
                te.pitch_changes = evt.pitch_changes 
                te.pitch_range = evt.pitch_range
                te.points = evt.points # type: ignore
                te.pitch_bend_active = len(evt.pitch_changes) > 0
                dialog.close()
                self.update_staff_and_tab()
                
            dialog.string_bend_selected.connect(on_apply)
            dialog.show()

    def _tuplet_chooser_selected(self, text):
        code = TUPLET_DISABLED
        if text != "":
            code = int(text.split()[0])
            (label, beats) = TupletTypes[code]
            self.track_model.tuplet_alteration(code, beats)
            
            # update and recalculate the measure presenter since
            # new tab events where likely created.
            evt = EditorEvent()
            evt.ev_type = EditorEvent.SYNC_MODEL_TO_VIEW
            evt.model = self.track_model 
            Signals.editor_event.emit(evt)

    def setTabEvent(self, tab_event : TabEvent):
        """
        set the tab cursor and react to any changes in data so 
        the toolbar reflects the state. 
        """ 
        # select buttons based on tab settings

        # set the matching duration
        dlist = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625]
        if tab_event.duration in dlist:
            i = dlist.index(tab_event.duration)
            btn = self._dur_btns[i]
            self._dur_grp.check_btn(btn) 

        for btn in self._stroke_btns:
            te = tab_event
            if btn.pvalue() == (te.upstroke,te.downstroke):
                self._stroke_grp.check_btn(btn)
                break

        if hasattr(te,"stroke_duration_index") and te.stroke_duration_index is not None:
            self._stroke_duration.setCurrentIndex(te.stroke_duration_index)   
        else:
            self._stroke_duration.setCurrentIndex(DefaultStrokeDurationIdx)
            te.stroke_duration_index = DefaultStrokeDurationIdx

        if te.render_dynamic: 
            for btn in self._dyn_btns:
                if btn.pvalue() == te.getDynamic():    
                    self._dyn_grp.check_btn(btn)
                    break

        # set dot
        if tab_event.tied_notes[tab_event.string]:
            btn = self._dot_btns[-1]
            self._dot_grp.check_btn(btn)
        elif tab_event.dotted:
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

        # set tuplet drop down.
        key = ""
        if tab_event.tuplet_code in TupletTypes:
            (label, _) = TupletTypes[tab_event.tuplet_code]
            key = f"{tab_event.tuplet_code} {label}"
        self._tuplet_chooser.setCurrentText(key)


    def __init__(self, track_model: Track, update_staff_and_tab):
        super().__init__()
        self.track_model = track_model 
                                         
        self._lookup = {}
        self.update_staff_and_tab = update_staff_and_tab
        self.setFixedHeight(75)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # not duration whole -> 64th  
        
        dur_container = ButtonGroupContainer("Duration")
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
            dur_container.add_item(btn)
        self.addWidget(dur_container) 

        self._dur_grp.selected.connect(self._on_duration_selected)
        self.addSeparator()

        # dotted notes that alter standard note durations
        dot_dur_container = ButtonGroupContainer("Special Duration")
        self._dot_grp = MutuallyExclusiveButtonGroup()
        
        self._dot_btns = (
            ToolbarButton(self, " ", "no dot", "clear-dots"),
            ToolbarButton(self, DOTTED, "dotted note", "dotted"),
            ToolbarButton(self, DOUBLE_DOTTED, "double dotted", "double-dotted"),
#            ToolbarButton(self, "3" + QUATER_NOTE, "triplet", "triplet"),
#            ToolbarButton(self, "5" + QUATER_NOTE, "quintuplet", "quintuplet"),
            ToolbarButton(self, u'\u1D17', "tied note", "tied-note")
        )
        for btn in self._dot_btns:
            self._dot_grp.addButton(btn)
            dot_dur_container.add_item(btn)

        triplet_label = QLabel()
        triplet_label.setText("Triplet: ")
        dot_dur_container.add_item(triplet_label)

        self._tuplet_chooser = QComboBox()
        self._tuplet_chooser.addItem("")
        for (tuplet_code,(label,beats)) in TupletTypes.items():
            text = f"{tuplet_code} {label}"
            self._tuplet_chooser.addItem(text)
        dot_dur_container.add_item(self._tuplet_chooser)

        self._tuplet_chooser.currentTextChanged.connect(self._tuplet_chooser_selected)

        self.addWidget(dot_dur_container)
        self._dot_grp.selected.connect(self._dot_selected) 
        self.addSeparator()

        stroke_container = ButtonGroupContainer("Chord Stroke")
        self._stroke_grp = MutuallyExclusiveButtonGroup()
        self._stroke_btns = (
            ToolbarButton(self, "", "no stroke", "stroke", (False,False)),
            ToolbarButton(self, UPSTROKE, "upstroke", "stroke", (True,False)),
            ToolbarButton(self, DOWNSTROKE, "downstroke", "stroke", (False,True))
        )
        self._stroke_duration = QComboBox()
        self._stroke_duration.setFixedWidth(60)
        opts = list(StrokeDurationMap.keys())
        self._stroke_duration.setToolTip('Stroke duration as a fraction of the note chord duration')
        self._stroke_duration.addItems(opts)
        self._stroke_duration.setCurrentIndex(opts.index(DefaultStrokeDuration))
        self._stroke_duration.currentIndexChanged.connect(self._on_stroke_direction_selected)
        for btn in self._stroke_btns:
            self._stroke_grp.addButton(btn)
            stroke_container.add_item(btn) 
        stroke_container.add_item(self._stroke_duration)    
        self.addWidget(stroke_container)
        self._stroke_grp.selected.connect(self._on_stroke_selected)
        self.addSeparator()


        # set dynamic
        dyn_container = ButtonGroupContainer("Dynamic")
        self._dyn_grp = MutuallyExclusiveButtonGroup()
        self._dyn_btns = ( 
            ToolbarButton(self, FORTE_SYMBOL * 3, Dynamic.tooltip(Dynamic.FFF), "dynamic", Dynamic.FFF),
            ToolbarButton(self, FORTE_SYMBOL * 2, Dynamic.tooltip(Dynamic.FF), "dynamic",Dynamic.FF),
            ToolbarButton(self, FORTE_SYMBOL, Dynamic.tooltip(Dynamic.F), "dynamic",Dynamic.F),
            ToolbarButton(self, MEZZO_SYMBOL + FORTE_SYMBOL, Dynamic.tooltip(Dynamic.MF), "dynamic",Dynamic.MF),
            ToolbarButton(self, MEZZO_SYMBOL + PIANO_SYMBOL, Dynamic.tooltip(Dynamic.MP), "dynamic",Dynamic.MP),
            ToolbarButton(self, PIANO_SYMBOL, Dynamic.tooltip(Dynamic.P), "dynamic",Dynamic.P),
            ToolbarButton(self, PIANO_SYMBOL * 2, Dynamic.tooltip(Dynamic.PP), "dynamic",Dynamic.PP),
            ToolbarButton(self, PIANO_SYMBOL * 3, Dynamic.tooltip(Dynamic.PPP), "dynamic",Dynamic.PPP)
        )
        for btn in self._dyn_btns:
            self._dyn_grp.addButton(btn) 
            dyn_container.add_item(btn)
        self.addWidget(dyn_container) 
        self._dyn_grp.selected.connect(self._dyn_selected)    
        self.addSeparator()

        art_container = ButtonGroupContainer("Articulation")        
        self._articulation_group = MutuallyExclusiveButtonGroup()
        self._articulation_btns = (
            ToolbarButton(self, NO_ARTICULATION, "no articulation", "clear-articulation"),
            ToolbarButton(self, LEGATO, "legato", "legato"),
            ToolbarButton(self, STACCATO, "staccato", "staccato")
        )
        for btn in self._articulation_btns:
            self._articulation_group.addButton(btn) 
            art_container.add_item(btn)
        self.addWidget(art_container)
        self._articulation_group.selected.connect(self._articulation_selected)    
        self.addSeparator()

        gest_container = ButtonGroupContainer("Hand efects")        
        self._hand_effects_group = MutuallyExclusiveButtonGroup() 
        self._hand_effects_btns = ( 
            ToolbarButton(self, " ", "no effects", "clear-hand-effects"),
            ToolbarButton(self, "bend", "bend", "bend-effect")
        )
        for btn in self._hand_effects_btns:
            self._hand_effects_group.addButton(btn) 
            gest_container.add_item(btn)
        self.addWidget(gest_container) 
        self._hand_effects_group.selected.connect(self._hand_effect_selected)
       
        (te,_) = self.track_model.current_moment()

        self.setTabEvent(te)
        self.addSeparator()






