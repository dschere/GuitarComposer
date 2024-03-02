""" 
A glyph is a musical symbol such as a staff a not a rest etc.

Glyphs are combined to create measures on a staff.
"""
from PyQt6.QtWidgets import QLabel, QApplication, QMainWindow
from PyQt6 import QtGui
from PyQt6.QtCore import Qt


WHOLE_NOTE = "𝅝 "
HALF_NOTE = "𝅗𝅥 "
QUATER_NOTE = "𝅘𝅥 "
EIGHT_NOTE = "𝅘𝅥𝅮 "
SIXTEENTH_NOTE = "𝅘𝅥𝅯 "
THRITYSEC_NOTE = "𝅘𝅥𝅰 "
SIXTYFORTH_NOTE = "𝅘𝅥𝅱 "
FLAT_SIGN = "♭ "
NATURAL_SIGN = "♮ "
SHARP_SIGN = "♯ "

BARLINE1 = "𝄀 "
BARLINE2 = "𝄁 "
END_REPEAT = "𝄂 "
START_REPEAT = "𝄃 "


TREBLE_CLEFF = "𝄞 "
DRUM_CLEFF = "𝄥 "
BASS_CLEFF = "𝄢 "

WHOLE_REST = "𝄻 "
HALF_REST = "𝄼 "
QUATER_REST = "𝄽 "
EIGHTH_REST = "𝄾 "
SIXTEENTH_REST = "𝄿 "
THRITYSEC_REST = "𝅀 "
SIXTYFORTH_REST = "𝅁 "

GHOST_NOTEHEAD = "𝅃 "


SymFontSize = {
    FLAT_SIGN: 24,
    SHARP_SIGN: 24,
    NATURAL_SIGN: 16,
    TREBLE_CLEFF: 64,
    DRUM_CLEFF: 48,
    BASS_CLEFF: 48,
    WHOLE_NOTE: 48
}
DEFAULT_SYM_FONT_SIZE = 32

STAFF_ABOVE_LINES = 7  # needed lines above staff
STAFF_BELOW_LINES = 7  # needed lines below staff
STAFF_LINE_SPACING = 20
STAFF_NUMBER_OF_LINES = 5  # number of permenant lines

STAFF_HEIGHT = (STAFF_ABOVE_LINES + STAFF_BELOW_LINES + STAFF_NUMBER_OF_LINES)\
    * STAFF_LINE_SPACING
STAFF_SYM_WIDTH = 40
# clef + bpm + key
STAFF_HEADER_WIDTH = 200

E2_MIDI_CODE = 40
E6_MIDI_CODE = 88

# map the y position of the staff to a midi note.
YPositionMidiTable = {}
MidiCode2Name = {}

def populate_lookup_table():
    global YPositionMidiTable
    n = ['e','f','f#','g','g#','a','a#','b','c','c#','d','d#']
    y_max = (STAFF_ABOVE_LINES + STAFF_BELOW_LINES + STAFF_NUMBER_OF_LINES) \
        * STAFF_LINE_SPACING
    i = 0
    y = y_max
    for midi in range(E2_MIDI_CODE,E6_MIDI_CODE+1):
        note_name = n[i]
        i = (i+1) % len(n)
        YPositionMidiTable[midi] = y - STAFF_LINE_SPACING + 5
        if len(note_name) == 1:
            y -= int(STAFF_LINE_SPACING/2)

populate_lookup_table()            



#TODO move this to a common place 
#################################################
def midicode_from_name(name):
    # starts at C1 which is midi code 24
    n = ['C','','D','','E','F','','G','','A','','B']
    
    # last character digit is the octave (E4 or F#4)
    octave = int(name[-1]) - 1
    offset = 24
    i = n.index(name[0])
    if name[1] == '#':
        i += 1
    if name[1] == 'b':
        i -= 1
    r = offset + (octave*12) + i
    return r    

KeyMidiCodeTable = {
    "C": [],
    "C#": [midicode_from_name("F#5"),
           midicode_from_name("C#5"),
           midicode_from_name("G#5"),
           midicode_from_name("D#5"),
           midicode_from_name("A#4"),
           midicode_from_name("E#5"),
           midicode_from_name("B#4"),
          ],
    "D": [],
    "D#": [],
    "E": [],
    "F": [
        midicode_from_name("Bb4")
    ]      
}


#################################################




class Canvas(QLabel):
    """
    Drawing canvas for music symbols, tablature and effects.

    This object is a collection of drawing routines. 
    """

    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height
        canvas = QtGui.QPixmap(width, height)
        canvas.fill(Qt.GlobalColor.white)
        self.setPixmap(canvas)
        self.canvas = canvas

        self.last_x, self.last_y = None, None
        self.pen_color = QtGui.QColor('#000000')

    # virtual method to be overloaded by children classes to call various
    # api comamnds below (draw_<operation> methods)
    def canvas_paint_event(self, painter):
        pass

    def draw_sign(self, painter, sign, x, midi_code):
        # can't figure out why its slightly off 
        y = YPositionMidiTable.get(midi_code,0)
        self.draw_symbol(painter, sign, x=x, y=y)

    def paintEvent(self, e):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.eraseRect(0, 0, self.width, self.height)
        self.canvas_paint_event(painter)
        painter.end()

    def draw_symbol(self, painter, sym, **opts):
        def_size = SymFontSize.get(sym, DEFAULT_SYM_FONT_SIZE)
        size = opts.get('size', def_size)
        # font with good Unicode support
        font = QtGui.QFont("DejaVu Sans", size)
        painter.setFont(font)
        x = opts.get('x', 0)
        y = opts.get('y', 0)
        painter.drawText(x, y, sym)

        # draw lines above/below staff as needed
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING 
        
        if y < top_line:
            line_y = top_line - STAFF_LINE_SPACING
            while y < line_y:
                print(f"{y} {line_y}")
                painter.drawLine(x-3, line_y, x+25, line_y )
                line_y -= STAFF_LINE_SPACING
            painter.drawLine(x-3, line_y, x+25, line_y )

        if y > bottom_line:
            line_y = bottom_line + STAFF_LINE_SPACING
            while y > line_y:
                painter.drawLine(x-3, line_y, x+25, line_y )
                line_y += STAFF_LINE_SPACING


    def draw_staff_background(self, painter):
        p = painter.pen()
        p.setWidth(1)
        p.setColor(self.pen_color)
        painter.setPen(p)

        offset = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        for line_num in range(STAFF_NUMBER_OF_LINES):
            y = line_num * STAFF_LINE_SPACING + offset
            #print(f"0 {y} {self.width} {y}")
            painter.drawLine(0, y, self.width, y)


class StaffHeaderGlyph(Canvas):
    def __init__(self, staff_symbol, staff_key):
        super().__init__(STAFF_HEADER_WIDTH, STAFF_HEIGHT)
        self.staff_symbol = staff_symbol
        self.staff_key = staff_key

    # use draw_ ... commands
    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)
        cleff_y_pos = STAFF_LINE_SPACING * \
            STAFF_ABOVE_LINES+SymFontSize[self.staff_symbol]
        self.draw_symbol(painter, self.staff_symbol, y=cleff_y_pos)

        x = 60
        key_codes = KeyMidiCodeTable.get(self.staff_key,[])

        sign = SHARP_SIGN
        if 'b' in self.staff_key or self.staff_key == 'F':
            sign = FLAT_SIGN 
        for midi_code in key_codes:
            self.draw_sign(painter, sign, x, midi_code)
            x += 10

        self.draw_sign(painter, WHOLE_NOTE, x, midicode_from_name("A3")) 
        
        


def unittest():
    import sys
    app = QApplication(sys.argv)

    # layout = QGridLayout()

    # c = Canvas(40,200)
    # c.setGeometry(0, 0, 40, 120)

    # c.draw_staff_background()
    # c.show()

    shg = StaffHeaderGlyph(TREBLE_CLEFF,"F")
    shg.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    unittest()
