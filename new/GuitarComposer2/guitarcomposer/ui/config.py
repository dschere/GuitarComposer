# TODO, this should be a config folder not theme, the theme 
# should mirror the config and overwrite ony fields that 
# specifc to the theme. 
#  Background, font etc. But mostly these variables should
#  be fixed.

from PyQt6.QtCore import Qt
from singleton_decorator import singleton

class _glyph:
    bg_color = Qt.GlobalColor.white
    
class _tablature_item:
    num_lines = 6
    line_spacing = 16
    text_font_size = 8
    width = 50
    height = 26 + (num_lines * line_spacing)
    y_start = 26
    text_font = "DejaVu Sans"

class _tablature_measure_divider(_tablature_item):
    def __init__(self):
        super().__init__()
        self.width = 10
        
class _staff_item:
    max_lines_above = 6
    max_lines_below = 6
    line_spacing = 13
    accent_spacing = 13
    text_font_size = 45
    accent_font_size = 20
    chord_stem_x = 29
    text_font = "DejaVu Sans"
    num_lines = 6
    width = 50
    font = "DejaVu Sans" # needed for music symbols 
    # computed ....
    height = 26 + (num_lines + max_lines_above + max_lines_below) * line_spacing
    y_start = 26 + max_lines_above * line_spacing

class _staff_header(_staff_item):
    def __init__(self):
        super().__init__()
        self.cleff_font_size = self.num_lines * self.line_spacing
        self.bpm_font_size = 8
        self.timesig_font_size = 3 * self.line_spacing
        
        self.cleff_x = 0
        self.bpm_x = 10
        self.timesig_x = 80
        self.keyid_notes_x = 120
        self.keyid_notes_x_inc = 15
        self.width = 300
        
class _staff_measure_divider(_staff_item):
    def __init__(self):
        super().__init__()
        self.width = 10
         

@singleton
class config:
    glyph = _glyph()
    staff_item = _staff_item()
    staff_header = _staff_header()
    staff_measure_divider = _staff_measure_divider()  
    tablature_item = _tablature_item()
    tablature_measure_dividor = _tablature_measure_divider()  
    
        
