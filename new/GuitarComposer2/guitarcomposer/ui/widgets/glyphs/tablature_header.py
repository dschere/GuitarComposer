from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox

from .glyph import glyph
from .note_renderer import note_renderer
from .constants import *

from guitarcomposer.ui.config import config
from guitarcomposer.common.midi_codes import midi_codes



class tablature_header(glyph):
    def __init__(self, tuning=None):
        self.config = config().tableture_header
        super().__init__(self.config.width, self.config.height)

        self.tuning_cboxes = [] 
        num_lines = self.config.num_lines
        for gstring_num in range(num_lines):
            combo_box = QComboBox(self)
            combo_box.addItems(midi_codes.generic_names())
            if tuning:
                combo_box.setCurrentText(tuning[gstring_num])
            self.tuning_cboxes.append(combo_box)
    
    def canvas_paint_event(self, painter):
        # draw staff lines using staff_item config
        self.parallel_lines(painter, self.config)

        y_start = self.config.y_start
        spacing = self.config.line_spacing
        num_lines = self.config.num_lines
        combo_width = self.config.combo_width
        combo_height = self.config.combo_height
        combo_x = 10
        offset = int(spacing/2)

        painter.drawText(combo_x, y_start - spacing, "Tuning")

        for gstring_num in range(num_lines):
            combo_y = y_start - offset + (spacing * gstring_num)
            
            combo_box = self.tuning_cboxes[gstring_num]
            
            combo_box.move(combo_x, combo_y)
            combo_box.setGeometry(combo_x, combo_y, combo_width, combo_height)
            combo_box.show()
