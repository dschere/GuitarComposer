"""

   +------------------------------------------------+
   |     toolbar that controls note duration, dynamic
   |     'hand' effects (bends etc.)
   +-------------------------------------------------
   | 1|2  grid of glyphs, each track represented as           |3|   
   |  |     by the following rows
   |  |   control header<intrument type> measure data items
   |  |   staff header, staff items
   |  |   tablature header, tablature items
   |  |   effect items
   |  | each track will have dividing lines
   
   1. small verticle list allowing to quickly select a track
   2. scrolling canvas of glyphs.
   3. output mixer volume and equalizer controls per track

 
"""
from PyQt6.QtWidgets import QApplication, QMainWindow, \
     QScrollArea, QVBoxLayout, QHBoxLayout, QWidget, QLabel

from guitarcomposer.ui.config import config

from .note_picker import note_picker


class score_editor_view(QWidget):
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # on the top a horizontal layout of control buttons
        # for duration, dynamic and performance.
        toolbar_layout = QHBoxLayout()
        
        
        
        # below is a horizontal layout
        content_layout = QHBoxLayout()
        
        main_layout.addLayout(toolbar_layout)
        main_layout.addLayout(content_layout)
    
    
    
    def __init__(self):
        super().__init__()
        self.init_ui()
