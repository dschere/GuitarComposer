import sys
from PyQt6.QtWidgets import QLabel, QGridLayout, QWidget
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

from guitarcomposer.ui.editor.controllers.note_duration_controller import note_duration_controller


class editor_view(QWidget):    
    def __init__(self, controller):
        super().__init__()
        
        #self.grid_layout = QGridLayout()
        #self.grid_layout.setSpacing(0)
        #self.grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        #self.grid_layout.setVerticalSpacing(0) 
        #self.setLayout(self.grid_layout)
        
        self.controller = controller
        
    def render_score(self, data):
        """ setup a previously created score in the editor.  
        """
        pass    
        
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        self.controler.key_press(key)
                
    def keyReleaseEvent(self, event: QKeyEvent):
        key = event.key()        
        self.controler.key_release(key)
        
        
        
