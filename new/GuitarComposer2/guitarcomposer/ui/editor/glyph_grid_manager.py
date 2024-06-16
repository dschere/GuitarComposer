""" 

This is the heart of the editor. The entire music score
is presented as a 2 grid of glyphs. The columns represent 
the number of beats and sub beats from the first measure.

Columns are created to hold the smallest duration of any track.

Each row of teh grid is a track (instrument)
"""
from PyQt6.QtWidgets import QApplication

from guitarcomposer.ui.widgets.glyphs import staff_header


class glyph_grid_manager:
    def __init__(self, parent):
        
        self.staffs = []
        self.grid = QGridLayout()
        parent.setLayout(grid)
        
        
    def add_staff_header(self, header):
        # a new staff header, a new row to the score
        staff = []
        row = len(self.staffs)
        self.glyphs.append(staff)
        self.grid.addWidget(header, row)  
        
        
        
