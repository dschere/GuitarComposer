from PyQt6 import QtGui
from PyQt6.QtWidgets import QLabel, QSizePolicy


from view.editor.glyphs.common import (FLAT_SIGN, 
                                       STAFF_LINE_SPACING, STAFF_ABOVE_LINES, STAFF_NUMBER_OF_LINES,
                                       YPositionMidiTable, SymFontSize, DEFAULT_SYM_FONT_SIZE,
                                       BEAT_ERROR_COLOR, BEAT_ERROR_FONT_SIZE, 
                                       BEAT_OVERFLOW_CHAR, BEAT_UNDERFLOW_CHAR
                                       )
from view.config import GuitarFretboardStyle
from singleton_decorator import singleton
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QRect, Qt

@singleton
class BeatErrorPresenter:
    def __init__(self):
        font = QtGui.QFont("DejaVu Sans", BEAT_ERROR_FONT_SIZE)
        font_metrics = QtGui.QFontMetrics(font)
        self.overflow_char_width = font_metrics.horizontalAdvance(BEAT_OVERFLOW_CHAR)
        self.text_height = int(font_metrics.height())
        self.underflow_char_width = font_metrics.horizontalAdvance(BEAT_UNDERFLOW_CHAR)
        self.font = font
        self.color = QtGui.QColor(*GuitarFretboardStyle.error)
            

    def draw(self, painter : QPainter, canvas):
        etext = canvas.beat_error
        char_width = {
            BEAT_OVERFLOW_CHAR: self.overflow_char_width,
            BEAT_UNDERFLOW_CHAR: self.underflow_char_width
        }[etext]
        count = int(canvas.width()/char_width)
        painter.setFont(self.font)
        painter.setPen(self.color)
        h = canvas.height() - self.text_height
        painter.drawText(0, h, canvas.beat_error * count)


class Canvas(QLabel):
    """
    Drawing canvas for music symbols, tablature and effects.

    This object is a collection of drawing routines. 
    """

    def __init__(self, width, height):
        super().__init__()
        self._highlight_background = False
        self.c_width = width
        self.c_height = height
        canvas = QtGui.QPixmap(width, height)
        pal = self.palette()

        canvas.fill(pal.window().color())
        self.setPixmap(canvas)
        self.canvas = canvas

        self.last_x, self.last_y = None, None
        # self.pen_color = pal.brightText().color()
        self.pen_color = QtGui.QColor(*GuitarFretboardStyle.string_color_rgb)

        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.beat_error = ""

    def beat_overflow_error(self):
        self.beat_error = BEAT_OVERFLOW_CHAR

    def beat_underflow_error(self):
        self.beat_error = BEAT_UNDERFLOW_CHAR

    def clear_beat_error(self):
        self.beat_error = ""    

    def draw_beat_error(self, painter):
        if len(self.beat_error) != 0:
            BeatErrorPresenter().draw(painter, self)

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

    def set_highlight(self):
        self._highlight_background = True
        self.update()

    def clear_highlight(self):
        self._highlight_background = False
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.eraseRect(0, 0, self.c_width, self.c_height)

        if self._highlight_background:
            painter.fillRect(0, 0, self.c_width, self.c_height,QColor(60,60,60))     
       
        self.canvas_paint_event(painter)
        self.draw_beat_error(painter)
        painter.end()

    def draw_ledger_line(self, painter, opts):
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

        if opts.get('italic') is not None:
            font.setItalic(True)    

        rgb = opts.get("color")
        if rgb:
            color = QtGui.QColor(*rgb)
            painter.setPen(color)

        x = opts.get('x', 0)
        y = opts.get('y', 0)
        painter.drawText(x, y, sym)
        if opts.get('draw_lines', True):
            self.draw_ledger_line(painter, opts)

    def draw_staff_background(self, painter):
        p = painter.pen()
        p.setWidth(1)
        p.setColor(self.pen_color)
        painter.setPen(p)

        offset = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        for line_num in range(STAFF_NUMBER_OF_LINES):
            y = line_num * STAFF_LINE_SPACING + offset
            painter.drawLine(0, y, self.c_width, y)
