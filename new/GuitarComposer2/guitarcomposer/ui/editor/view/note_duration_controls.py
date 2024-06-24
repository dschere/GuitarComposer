"""
Control bar that is on the top of the editor allowing for 
selecting the current duration, dynamic and hand effects
for a note. 
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel


from guitarcomposer.ui.widgets.note_picker import note_picker
from guitarcomposer.ui.widgets.dynamic_control import dynamic_control
from guitarcomposer.ui.widgets.duration_control import duration_control

from guitarcomposer.ui.widgets.glyphs.constants import *

from guitarcomposer.ui.widgets.glyphs.constants import QUATER_REST
from guitarcomposer.common import dynamic as dyn

from guitarcomposer.common.event_subsys import EventSubSys, DYNAMIC_SELECTED, NOTE_SELECTED


class note_duration_controls(QWidget):
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(150)
        self.setMaximumWidth(500)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        grid_layout.setVerticalSpacing(0) 
        self.setLayout(grid_layout)


        dc = dynamic_control(self.on_dynamic_selected)
        grid_layout.addWidget(dc, 0, 0)
        dc.select(dyn.MF)

        dur_ctl = duration_control(self.on_note_selected)
        grid_layout.addWidget(dur_ctl, 0, 1)  
        dur_ctl.select(QUATER_REST)
        
    def on_dynamic_selected(self, dyn_text, dyn_value):
        EventSubSys.publish(DYNAMIC_SELECTED, (dyn_text,dyn_value))
        
    def on_note_selected(self, selected):
        EventSubSys.publish(NOTE_SELECTED, selected)
        
           
        
