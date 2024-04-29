from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QTimer

from .glyph import glyph
from .constants import *
from .note_renderer import note_renderer

from guitarcomposer.common import durationtypes as DT
from guitarcomposer.ui.config import config


class tablature_item(glyph):
    """
    
    gstring 1 (highest) 
      ---- 
      
      -10-    <-- fret number
      
      --9-
      
      ----
      
      ----
      
    gstring 6  (lowest)
      ----
      
    """
    
    def __init__(self, tabNotes=[], gstring_selected=None):
        self.config = config().tablature_item
        super().__init__(self.config.width, self.config.height)
        # index 0 maps to gstring 1 
        self.gstring_table = [None] * self.config.num_lines
        self.gstring_selected = gstring_selected
        
        for (fret, idx) in tabNotes:
            self.gstring_table[idx] = fret
            
        
    def canvas_paint_event(self, painter):
        # draw tab lines for each string
        self.parallel_lines(painter, self.config)
        
        y_start = self.config.y_start
        spacing = self.config.line_spacing
        offset = int(spacing/2)
        box_width = self.config.box_width

        size = self.config.line_spacing
        text_font_size = self.config.text_font_size
        text_font = self.config.text_font
        font = QtGui.QFont(text_font, text_font_size)
        font.setBold(True)
        painter.setFont(font)

        
        x = int(self.config.width/2 - self.config.text_font_size/2) + 3
                
        # render fret numbers on guitar string lines
        for (idx, fret) in enumerate(self.gstring_table):
            if fret:
                y = y_start - 3 + (idx * spacing) + offset
                y1 = y_start - offset + (idx * spacing)
                # erase portion of tab line so text is readable
                painter.eraseRect(x,y1,box_width, spacing)
                # draw text
                painter.drawText(x,y, str(fret))
                
        if self.gstring_selected:
            idx = self.gstring_selected
            y1 = y_start - offset + (idx * spacing)
            painter.eraseRect(x,y1,box_width, spacing)            
            painter.drawRect(x,y1,box_width, spacing)
        
    def erase_fret_string(self,  fret, idx):
        self.gstring_table[idx] = None
        self.update()
        
    def set_fret_string(self, fret, idx):        
        self.gstring_table[idx] = fret
        self.update()
        
    def set_select_box(self, gstring):
        self.gstring_selected = gstring
        self.update()

    def disable_select_box(self, gstring):
        self.gstring_selected = None
        self.update()

    def getData(self):
        return self.gstring_table
