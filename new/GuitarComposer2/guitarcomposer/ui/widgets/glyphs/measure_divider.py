from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *

from guitarcomposer.ui.config import config


class measure_divider(glyph):
    def __init__(self, config, linetype):
        # grab config for this class
        super().__init__(config.width, config.height)
        self.linetype = linetype
        self.config = config
        

    def canvas_paint_event(self, painter):
        # draw staff lines using staff_item config
        self.parallel_lines(painter, self.config)
        
        text_font = self.config.text_font       
        line_spacing = self.config.line_spacing
        num_lines = self.config.num_lines
        y_start = self.config.y_start
        size = line_spacing * (num_lines-1)
        
        font = QtGui.QFont(text_font, size)
        painter.setFont(font)
        
        y = y_start + size
        painter.drawText(0, y, self.linetype)
 
