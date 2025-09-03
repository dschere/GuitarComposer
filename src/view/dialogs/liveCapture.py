""" 
Controls the live audio capture thread and optional 
effects.
"""
from services.synth.synthservice import synthservice
from view.dialogs.effectsControlDialog.dialog import EffectsDialog

from PyQt6.QtWidgets import (QDialog, QGridLayout, 
        QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
        QCheckBox, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMessageBox)

class LiveCaptureDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)



