import sys
from PyQt6.QtWidgets import QLabel, QGridLayout, QWidget, QSizePolicy
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

from guitarcomposer.ui.editor.controllers.note_duration_controller import note_duration_controller
from guitarcomposer.common.event_subsys import EventSubSys, KEY_PRESS, KEY_RELEASE


from guitarcomposer.ui.widgets.glyphs.staff_item import staff_item
from guitarcomposer.ui.widgets.glyphs.staff_header import staff_header
from guitarcomposer.ui.widgets.glyphs.staff_measure_divider import staff_measure_divider
from guitarcomposer.ui.widgets.glyphs.tablature_measure_divider import tablature_measure_divider
from guitarcomposer.ui.widgets.glyphs.tablature_item import tablature_item
from guitarcomposer.ui.widgets.glyphs.tablature_header import tablature_header
from guitarcomposer.ui.widgets.glyphs.effect_item import effect_item

from guitarcomposer.ui.widgets.glyphs.constants import *

from guitarcomposer.common.durationtypes import *

from guitarcomposer.common.midi_codes import midi_codes


class editor_view(QWidget):    
    def __init__(self):
        super().__init__()
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        self.grid_layout.setVerticalSpacing(0) 
        self.setLayout(self.grid_layout)
        
    def render_score(self, s_model):
        """ setup a previously created score in the editor.  
        """
        for (tnum,(track_name, t_model)) in enumerate(s_model.tracks.items()):
            staff_row = tnum * 3
            tab_row = staff_row + 1
            eff_row = tab_row + 1
            
            header = staff_header(t_model.cleff, \
                s_model.bpm, t_model.timesig, \
                    midi_codes.get_staff_accents(s_model.key) )
                    
            self.grid_layout.addWidget(\
                header , staff_row, 0) 
                    
        
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        EventSubSys.publish(KEY_PRESS, (self, key))
                
    def keyReleaseEvent(self, event: QKeyEvent):
        key = event.key()        
        EventSubSys.publish(KEY_RELEASE, (self, key))
        
        
        
