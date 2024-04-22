from PyQt6.QtCore import Qt
from singleton_decorator import singleton

class _glyph:
    bg_color = Qt.GlobalColor.white
    
class _staff_item:
    max_lines_above = 6
    max_lines_below = 6
    line_spacing = 15
    accent_spacing = 13
    text_font_size = 45
    accent_font_size = 20
    chord_stem_x = 29
    text_font = "DejaVu Sans"
    num_lines = 6
    width = 50
    font = "DejaVu Sans" # needed for music symbols 
    # computed ....
    height = (num_lines + max_lines_above + max_lines_below) * line_spacing
    y_start = max_lines_above * line_spacing

@singleton
class theme:
    glyph = _glyph()
    staff_item = _staff_item()
    
    
    
        
