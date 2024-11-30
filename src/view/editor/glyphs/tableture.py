
from PyQt6.QtGui import QColor
from view.editor.glyphs.canvas import Canvas
from view.editor.glyphs.common import (STAFF_SYM_WIDTH,
                                       STAFF_HEIGHT, TABLATURE_LINE_SPACE, TABLATURE_NUM_LINES
                                       )

from view.config import GuitarFretboardStyle
from view.editor.glyphs.ornamental_markings import oramental_markings


class TabletureGlyph(Canvas):
    CURSOR_COLOR = QColor(*GuitarFretboardStyle.scale_root_color_rgb)
    TEXT_COLOR = QColor(*GuitarFretboardStyle.orament_color_rgb)

    def __init__(self):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT+15)
        # Note: gstring is from 1-6
        self._cursor = None  # type: ignore # None | gstring
        # (gstring) -> (fret, **options)
        self.tab_notes = {}

    def clear_cursor(self):
        self._cursor = None  # type: ignore
        self.update()

    def set_cursor(self, gstring):
        self._cursor = gstring
        self.update()  # schedule a repaint

    def set_tab_note(self, gstring, fret, **opts):
        self.tab_notes[gstring] = (fret, opts)
        self.update()

    def clear_tab_note(self, gstring):
        del self.tab_notes[gstring]
        self.update()

    def draw_tableture_backround(self, painter):
        p = painter.pen()
        p.setWidth(1)
        p.setColor(self.pen_color)
        painter.setPen(p)

        offset = 15
        for line_num in range(TABLATURE_NUM_LINES):
            y = line_num * TABLATURE_LINE_SPACE + offset
            # print(f"0 {y} {self.width} {y}")
            painter.drawLine(0, y, self.width(), y)

    def draw_cursor(self, painter):
        p = painter.pen()
        p.setWidth(2)
        p.setColor(self.CURSOR_COLOR)
        painter.setPen(p)

        # Must be called before draw_tab_notes
        gstring = self._cursor
        assert gstring != None
        x = int(self.c_width * 0.22)
        width = int(2*self.c_width/3)
        n = gstring  # type: ignore
        y = (n * TABLATURE_LINE_SPACE) + int(3 * TABLATURE_LINE_SPACE/10)

        # print("painter.drawRect(%d,%d,%d,%d)" % (x, y+4, width, width-4))
        painter.drawRect(x, y, width, width-4)

        if self.tab_notes.get(gstring):
            # erase interior to make the numbers or 'x'
            # more readable
            painter.eraseRect(x+1, y+1, width-1, width-1)

    def draw_tab_notes(self, painter, gstring, fret, opts):
        x = int(self.c_width/4)
        width = int(self.c_width/2)
        y = gstring * TABLATURE_LINE_SPACE
        painter.eraseRect(x+1, y+1, width-1, width-1)
        if fret != -1:
            sym_color = GuitarFretboardStyle.orament_color_rgb
            self.draw_symbol(painter, str(fret),
                             draw_lines=False,
                             x=x,
                             y=y+TABLATURE_LINE_SPACE +
                             int(TABLATURE_LINE_SPACE/2),
                             bold=True,
                             size=TABLATURE_LINE_SPACE-2,
                             color=sym_color)

    def canvas_paint_event(self, painter):
        self.draw_tableture_backround(painter)
        self.draw_cursor(painter)

        for (gstring, (fret, opts)) in self.tab_notes.items():
            self.draw_tab_notes(painter, gstring, fret, opts)

