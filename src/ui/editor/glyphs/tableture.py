from .canvas import *


class TabletureGlyph(Canvas):
    def __init__(self):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT)
        # Note: gstring is from 1-6
        self.cursor = None # None | gstring
        # (gstring) -> (fret, **options)
        self.tab_notes = {}

    def clear_cursor(self):
        self.cursor = None
        self.update()

    def set_cursor(self, gstring):
        self.cursor = gstring
        self.update() # schedule a repaint

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

        offset = 0
        for line_num in range(TABLATURE_NUM_LINES):
            y = line_num * TABLATURE_LINE_SPACE + offset
            #print(f"0 {y} {self.width} {y}")
            painter.drawLine(0, y, self.width, y)

    def draw_cursor(self, painter):
        p = painter.pen()
        p.setWidth(2)
        p.setColor(self.pen_color)
        painter.setPen(p)

        # Must be called before draw_tab_notes 
        gstring = self.cursor
        x =int(self.width/4)
        width = int(self.width/2)
        y = (TABLATURE_NUM_LINES - gstring - 1) * TABLATURE_LINE_SPACE + int(TABLATURE_LINE_SPACE/2)

        painter.drawRect(x, y+4, width, width-4)

        if self.tab_notes.get(gstring):
            # erase interior to make the numbers or 'x'
            # more readable
            painter.eraseRect(x+1,y+1,width-1,width-1)    

    def draw_tab_notes(self, painter, gstring, fret, opts):
        x =int(self.width/4)
        width = int(self.width/2)
        y = (TABLATURE_NUM_LINES - gstring - 1) * TABLATURE_LINE_SPACE 
        #if gstring == self.cursor:
        painter.eraseRect(x+1,y+1,width-1,width-1)    
        self.draw_symbol(painter, str(fret),
            draw_lines=False, 
            x=x+2, 
            y=y+TABLATURE_LINE_SPACE+int(TABLATURE_LINE_SPACE/2), 
            bold = True,
            size=TABLATURE_LINE_SPACE-2,
            color=(255,0,0) )

    def canvas_paint_event(self, painter):
        self.draw_tableture_backround(painter)
        if self.cursor:
            self.draw_cursor(painter)

        for (gstring, (fret, opts)) in self.tab_notes.items():
            self.draw_tab_notes(painter, gstring, fret, opts) 

