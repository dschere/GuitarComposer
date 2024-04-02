from .canvas import * 

class StaffGlyph(Canvas):
    def __init__(self):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT)
    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)

class StaffHeaderGlyph(Canvas):
    def __init__(self, symbol, key, timesig, bpm):
        super().__init__(STAFF_HEADER_WIDTH, STAFF_HEIGHT)
        self.staff_symbol = symbol
        self.staff_key = key
        self.staff_timesig = timesig
        self.staff_bpm = bpm

    # use the draw_ ... commands
    def canvas_paint_event(self, painter):
        # draw background lines
        self.draw_staff_background(painter)

        # draw beats per minute
        y = (STAFF_LINE_SPACING * STAFF_ABOVE_LINES) - STAFF_LINE_SPACING
        bpm = self.staff_bpm
        self.draw_symbol(painter, f"{QUATER_NOTE} = {bpm}", 
            size=12, draw_lines=False, x=0, y=y)

        # draw staff
        cleff_y_pos = STAFF_LINE_SPACING * \
            STAFF_ABOVE_LINES+SymFontSize[self.staff_symbol]
        self.draw_symbol(painter, self.staff_symbol, y=cleff_y_pos)

        # draw time signature
        ts = self.staff_timesig.split('/')
        num_y = (STAFF_ABOVE_LINES * STAFF_LINE_SPACING) + 24
        den_y = num_y + (STAFF_LINE_SPACING * 2) + 8
        self.draw_symbol(painter, ts[0], x=60, y=num_y) 
        self.draw_symbol(painter, ts[1], x=60, y=den_y) 

        # draw accents (sharps and flat) based on the key
        x = 100
        key_codes = KeyMidiCodeTable.get(self.staff_key,[])

        sign = SHARP_SIGN
        if 'b' in self.staff_key or self.staff_key == 'F':
            sign = FLAT_SIGN 
        for midi_code in key_codes:
            self.draw_sign(painter, sign, x, midi_code)
            x += 10

        # draw the two verticle lines that mark the end of the
        # the staff header
        x += 7
        size = ((STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING) 
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING
        self.draw_symbol(painter, BARLINE2, x=x, y=bottom_line, size=size) 
        
