from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *

from guitarcomposer.ui.config import config


class staff_measure_divider(glyph):
    def __init__(self, linetype):
        # grab config for this class
        self.config = config().staff_item
        super().__init__(self.config.width, self.config.height)
        self.linetype = linetype

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
 
