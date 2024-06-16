"""

   +------------------------------------------------+
   |     toolbar that controls note duration, dynamic
   |     'hand' effects (bends etc.)
   +-------------------------------------------------
   |  |  grid of glyphs, each track represented as              
   |  |     by the following rows
   |  |   control header<intrument type> measure data items
   |  |   staff header, staff items
   |  |   tablature header, tablature items
   |  |   effect items
   |  | each track will have dividing lines
   
 
"""
from PyQt6.QtWidgets import QApplication, QMainWindow, \
     QScrollArea, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy
from PyQt6.QtCore import Qt

from guitarcomposer.ui.config import config
from guitarcomposer.ui.widgets.glyphs.constants import *


from .dynamic_control import dynamic_control
from .duration_control import duration_control
from .note_picker import note_picker



class score_editor_view(QWidget):
    
    def init_ui(self, controller):
        
        main_layout = QVBoxLayout()
        
        # on the top a horizontal layout of control buttons
        # for duration, dynamic and performance.
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(5)
        
        
        self.dyn_ctl = dynamic_control(controller.dynamic_event)             
        self.dur_ctl = duration_control(controller.duaration_event)    
        self.sub_dur_ctl = note_picker(
            [
               {'text': TRIPLET, 'tooltip':'Triplet'},
               {'text': QUINTUPLET  , 'tooltip':'Quintuplet'},
               {'text': DOTTED, 'tooltip': 'Dotted note'},
               {'text': DOUBLE_DOTTED, 'tooltip': 'Double dotted note'}
            ],
            controller.subbeat_duration_event, 
            True, 
            max_buttons_per_column=2,
            size=48,
            hover_size=52,
            hover_font_size_change=False,
            title="FRACTIONAL BEAT"
        )
                
        toolbar_layout.addWidget(self.dyn_ctl, 0, \
            Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.dur_ctl, 0, \
            Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.sub_dur_ctl, 0, \
            Qt.AlignmentFlag.AlignLeft)
            
        # below is a horizontal layout
        content_layout = QHBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        n = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        scroll_area.setHorizontalScrollBarPolicy(n)  # Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        scroll_area.setVerticalScrollBarPolicy(n)    # Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(scroll_area)
        
        
        self.setLayout(main_layout)
        
        
    
    
    def __init__(self, controller):
        super().__init__()
        self.init_ui(controller)


