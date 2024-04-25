"""

track_glyph
  |
  +-- staff 
        |
        +--- staff_header
        +--- staff_note
        +--- staff_rest
        +--- staff_chord        
        +--- staff_end_measure
        +--- staff_end_repeat
        +--- staff_begin_repeat                   
  +--- tableture
        |
        +--- tableture_header
        +--- tableture_item
        +--- tableture_end_measure 
  +--- effects
        |
        +--- effects_header
        +--- effects_item

"""
from PyQt6.QtWidgets import QLabel
from PyQt6 import QtGui
from PyQt6.QtCore import Qt


from guitarcomposer.ui.config import config



class glyph(QLabel):
    """ 
    1. provide a painter object for derived classes
    2. provide common methods used.
    """

    def __init__(self, width, height):
        """
        width and hight in pixels
        kw_args
            bg_color -> default white
        """
        super().__init__()
        self._width = width
        self._height = height
        canvas = QtGui.QPixmap(width, height)
        bg_color = config().glyph.bg_color

        canvas.fill(bg_color)
        self.setPixmap(canvas)
        self.canvas = canvas
        self.setFixedSize(width, height)

    def canvas_paint_event(self, painter):
        """
        Overload this method to use member functions to 
        draw music engraving 
        """

    def paintEvent(self, e):
        "QLabel paint event handler"
        painter = QtGui.QPainter()
        painter.begin(self)
        # clear anything that was there
        painter.eraseRect(0, 0, self._width, self._height)

        # build up image
        self.canvas_paint_event(painter)
        painter.end()

    def parallel_lines(self, painter, conf):
        line_spacing = conf.line_spacing
        num_lines = conf.num_lines
        y_start = conf.y_start

        for i in range(num_lines):
            y = y_start + (line_spacing * i)
            painter.drawLine(0, y, self._width, y)
