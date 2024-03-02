#!/usr/bin/env python3
"""  

Creates an editor for a score.

Each staff is a row
  There are 3 rows per track
  
  staff (traditional notation)
  tablature (guitar string/fret)
  effects (markers indicating changes in audio effects)


"""
from PyQt6.QtWidgets import QWidget, QGridLayout





class Staff(QWidget):
    def __init__(self):
        super().__init__()
        

class Track:
    def __init__(self):
        self.staff = []
        self.tablature = []
        self.effects = []
        


class SongEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.num_measures = 0
        self.tracks = []
        self.layout = QGridLayout()
        self.setLayout(self.layout)