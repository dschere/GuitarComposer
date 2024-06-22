"""
high level widget that contains all the controls and all tracks of 
a peice.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from guitarcomposer.ui.editor.view.editor_view import editor_view 
from guitarcomposer.ui.editor.view.note_duration_controls import note_duration_controls

class score(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()

        layout.addWidget(note_duration_controls())
        layout.addWidget(editor_view())
        

        self.setLayout(layout)
