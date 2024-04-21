from PyQt6.QtCore import Qt
from singleton_decorator import singleton

class _glyph:
    bg_color = Qt.GlobalColor.white
    
class _staff_item:
    max_lines_above = 6
    max_lines_below = 6
    line_spacing = 30
    accent_spacing = 13
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
    
    
    
        
