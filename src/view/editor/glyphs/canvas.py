from PyQt6 import QtGui
from PyQt6.QtWidgets import QLabel


from view.editor.glyphs.common import (FLAT_SIGN,
                                       STAFF_LINE_SPACING, STAFF_ABOVE_LINES, STAFF_NUMBER_OF_LINES,
                                       YPositionMidiTable, SymFontSize, DEFAULT_SYM_FONT_SIZE)
from view.config import GuitarFretboardStyle

class Canvas(QLabel):
    """
    Drawing canvas for music symbols, tablature and effects.

    This object is a collection of drawing routines. 
    """

    def __init__(self, width, height):
        super().__init__()
        self.c_width = width
        self.c_height = height
        canvas = QtGui.QPixmap(width, height)
        pal = self.palette()

        canvas.fill(pal.window().color())
        self.setPixmap(canvas)
        self.canvas = canvas

        self.last_x, self.last_y = None, None
        #self.pen_color = pal.brightText().color()
        self.pen_color = QtGui.QColor(*GuitarFretboardStyle.string_color_rgb)

        self.setFixedWidth(width)
        self.setFixedHeight(height)


    # virtual method to be overloaded by children classes to call various
    # api comamnds below (draw_<operation> methods)
    def canvas_paint_event(self, painter):
        pass

    def draw_sign(self, painter, sign, x, midi_code):
        y = YPositionMidiTable.get(midi_code, 0)
        if sign == FLAT_SIGN:
            y -= int(STAFF_LINE_SPACING/2)
        self.draw_symbol(painter, sign, x=x, y=y)

    def draw_note(self, painter, x, midi_code):
        pass

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.eraseRect(0, 0, self.c_width, self.c_height)
        self.canvas_paint_event(painter)
        painter.end()

    def draw_out_of_bounds_line(self, painter, opts):
        x = opts.get('x', 0)
        y = opts.get('y', 0)
        # draw lines above/below staff as needed
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING

        if y < top_line:
            line_y = top_line - STAFF_LINE_SPACING
            while y < line_y:
                painter.drawLine(x-3, line_y, x+25, line_y)
                line_y -= STAFF_LINE_SPACING
            painter.drawLine(x-3, line_y, x+25, line_y)

        if y > bottom_line:
            line_y = bottom_line + STAFF_LINE_SPACING
            while y > line_y:
                painter.drawLine(x-3, line_y, x+25, line_y)
                line_y += STAFF_LINE_SPACING

    def draw_symbol(self, painter, sym, **opts):
        def_size = SymFontSize.get(sym, DEFAULT_SYM_FONT_SIZE)
        size = opts.get('size', def_size)
        # font with good Unicode support
        font = QtGui.QFont("DejaVu Sans", size)
        painter.setFont(font)

        if opts.get('bold'):
            font.setBold(True)

        rgb = opts.get("color")
        if rgb:
            color = QtGui.QColor(*rgb)
            painter.setPen(color)

        x = opts.get('x', 0)
        y = opts.get('y', 0)
        painter.drawText(x, y, sym)
        if opts.get('draw_lines', True):
            self.draw_out_of_bounds_line(painter, opts)

    def draw_staff_background(self, painter):
        p = painter.pen()
        p.setWidth(1)
        p.setColor(self.pen_color)
        painter.setPen(p)

        offset = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        for line_num in range(STAFF_NUMBER_OF_LINES):
            y = line_num * STAFF_LINE_SPACING + offset
            painter.drawLine(0, y, self.c_width, y)
