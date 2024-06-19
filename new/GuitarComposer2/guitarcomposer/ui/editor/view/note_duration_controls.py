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
from guitarcomposer.ui.editor.controllers.note_duration_controller import note_duration_controller



class note_duration_controls(QWidget):
    def __init__(self, controller: note_duration_controller):
        super().__init__()
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setHorizontalSpacing(0)  # Set horizontal spacing to zero
        grid_layout.setVerticalSpacing(0) 
        self.setLayout(grid_layout)


        dc = dynamic_control(controller.dynamic_selected)
        grid_layout.addWidget(dc, 0, 0)
        dc.select(dyn.MF)

        dur_ctl = duration_control(controller.note_selected)
        grid_layout.addWidget(dur_ctl, 0, 1)  
        dur_ctl.select(QUATER_REST)
        

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys
    
     
     
    app = QApplication(sys.argv)
    c = note_duration_controller()
    window = note_duration_controls(c)
    window.show()
    sys.exit(app.exec())


