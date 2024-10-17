"""
Central place for custom signals/slots for the application
"""
from PyQt6.QtCore import QObject, pyqtSignal
from singleton_decorator import singleton


class ScaleSelectedEvent:
    def __init__(self):
        self.scale_midi = []
        self.scale_seq = []
        self.key = ""


@singleton
class _Signals(QObject):
    scale_selected = pyqtSignal(ScaleSelectedEvent)


Signals = _Signals()
    
