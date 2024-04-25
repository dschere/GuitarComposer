"""
This is the protion of the staff that contains the 
cleff, beats per minutes, timesignature and key.


small font note = <bpm>

cleff  timesig  key  
"""
from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .note_renderer import note_renderer
from .constants import *

from guitarcomposer.ui.config import config


class staff_header(glyph):
    def __init__(self, cleff, bpm, timesig, accented_notes):
        self.config = config().staff_header
        super().__init__(self.config.width, self.config.height)

        self.accented_notes = accented_notes
        self.timesig = timesig
        self.cleff = cleff
        self.bpm = bpm 
    
    def canvas_paint_event(self, painter):
        # draw staff lines using staff_item config
        self.parallel_lines(painter, self.config)
        nr = note_renderer(self.cleff)

        text_font = self.config.text_font
        line_spacing = self.config.line_spacing
        num_lines = self.config.num_lines
        y_start = self.config.y_start
        

        cleff_y = y_start + (num_lines * line_spacing)  
        bpm_y = y_start - (line_spacing * 2)
        
        # draw the cleff
        cleff_font_size = self.config.cleff_font_size
        font = QtGui.QFont(text_font, cleff_font_size)
        painter.setFont(font)
        
        painter.drawText(self.config.cleff_x, cleff_y, self.cleff)
        
        # draw bpm above the cleff
        bpm_font_size = self.config.bpm_font_size
        font = QtGui.QFont(text_font, bpm_font_size)
        painter.setFont(font)
        
        bpm_text = QUATER_NOTE + " = " + str(self.bpm)
        
        painter.drawText(self.config.bpm_x, bpm_y, bpm_text)
        
        # draw time signature
        timesig_font_size = self.config.timesig_font_size
        font = QtGui.QFont(text_font, timesig_font_size)
        painter.setFont(font)
        x = self.config.timesig_x
        
        painter.drawText(x, y_start + timesig_font_size - 3, \
            str(self.timesig[0]) )
        
        painter.drawText(x, y_start + (timesig_font_size*2) + 3, \
            str(self.timesig[1]) )

        # draw accents on bars to indicate our key
        x = self.config.keyid_notes_x
        for (accent, midi_code) in self.accented_notes:
            nr.draw_note_accent(painter,\
               self.config, midi_code, accent, x)
            x += self.config.keyid_notes_x_inc
