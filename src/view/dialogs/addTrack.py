""" 
In response to an add track being clicked.

qdialog
  layout
    (future)
    type:
       midi instrument
       (future) midi drum
       (future) audio clips
       (future) modulator

    instrument
    key (default song)
    time signiture (default song time sig)
    beat (default song beat)

"""
from PyQt6.QtWidgets import (QDialog, QGridLayout, QApplication,
        QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
        QCheckBox, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt
from view.events import Signals


class AddTrackDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        
