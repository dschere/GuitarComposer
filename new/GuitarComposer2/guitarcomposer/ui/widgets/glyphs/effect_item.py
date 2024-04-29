from PyQt6 import QtGui
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from .glyph import glyph
from .constants import *
from .note_renderer import note_renderer

from guitarcomposer.ui.config import config


class effect_item(glyph):

    def __init__(self):
        self.config = config().effect_item
        super().__init__(self.config.width, self.config.height)
        self.color = 'grey'
        self.selected = False
        self.settings = None
        
    def mousePressEvent(self, event):
        if not self.selected:
            # show effects dialog and get settings, if user selects
            # apply then change state
            self.selected = True
            self.color = 'green'
            self.update()
        else:
            # show effects dialog, if user selects disable
            # toggle selected 
            self.selected = False
            self.color = 'grey'
            self.update()
            
        print(self.selected)        
    
    def canvas_paint_event(self, painter):
        rect_width = self.config.rect_width
        rect_height = self.config.rect_height
        rect_angle = 45  # Rotation angle in degrees
        rect_color = QColor("gold")
        rect_pen = QPen(rect_color, 3, Qt.PenStyle.SolidLine)
        rect_brush_color = QColor(self.color)  # Fill color
        
        x1 = 0
        y1 = int(self.config.height/2)
        x2 = self.config.width
        y2 = y1
        painter.drawLine(x1, y1, x2, y2)


        # Translate and rotate the painter to draw the rotated rectangle
        painter.translate(self.width() // 2, self.height() // 2)  # Center the drawing
        painter.rotate(rect_angle)
        
        # Set the pen and brush for drawing
        painter.setPen(rect_pen)
        painter.setBrush(rect_brush_color)  # Set the fill color
        
        # Draw the rotated rectangle
        painter.drawRect(-rect_width // 2, -rect_height // 2, rect_width, rect_height)


         
