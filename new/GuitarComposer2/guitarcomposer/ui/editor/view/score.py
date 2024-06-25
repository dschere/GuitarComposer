"""
high level widget that contains all the controls and all tracks of 
a peice.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from guitarcomposer.ui.editor.view.editor_view import editor_view 
from guitarcomposer.ui.editor.view.note_duration_controls import note_duration_controls

class score(QWidget):
    
    def get_editor(self):
        return self.ew
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.ew = editor_view()

        # control note duration, dynamic and hadn effects
        layout.addWidget(note_duration_controls(), alignment=Qt.AlignmentFlag.AlignLeft)
        # music notation and tableture along with effect control
        layout.addWidget(self.ew, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # navigation of score
        
        self.setLayout(layout)
