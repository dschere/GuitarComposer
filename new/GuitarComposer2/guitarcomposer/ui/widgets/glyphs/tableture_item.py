from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *
from .note_renderer import note_renderer

from guitarcomposer.common import durationtypes as DT
from guitarcomposer.ui.config import config


class tableture_item(glyph):
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
    
    def __init__(self):
        self.config = config().tablature_item
        super().__init__(self.config.width, self.config.height)
        # index 0 maps to gstring 1 
        self.gstring_table = [None] * self.config.num_lines
        self.gstring_selected = None
        
        
    def canvas_paint_event(self, painter):
        self.parallel_lines(painter, self.config)
        
        y_start = self.config.y_start
        spacing = self.config.line_spacing
        offset = int(spacing/2)
        
        x = int(self.config.width/2 - self.config.text_font_size/2)
                
        # render fret numbers on guitar string lines
        for (idx, fret) in enumerate(self.gstring_table):
            if fret:
                y = y_start + (idx * spacing) + offset
                painter.drawText(x, y, str(fret))
                
        if self.gstring_selected:
            gstring = self.gstring_selected
            idx = gstring - 1 
            y1 = y_start - offset + (idx * spacing)
            y2 = y_start + offset + (idx * spacing)
            painter.drawRect(0, y1, self.config.width, y2)
        
    def erase_fret_string(self,  fret, gstring):
        self.gstring_table[gstring-1] = None
        self.update()
        
    def set_fret_string(self, fret, gstring):        
        self.gstring_table[gstring-1] = fret
        self.update()
        
    def set_select_box(self, gstring):
        self.gstring_selected = gstring
        self.update()

    def disable_select_box(self, gstring):
        self.gstring_selected = None
        self.update()

    def getData(self):
        return self.gstring_table
