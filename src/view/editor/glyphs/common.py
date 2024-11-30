# common impprts and variables
# from PyQt6.QtWidgets import QLabel, QApplication, QMainWindow, QGridLayout, QWidget
# from PyQt6 import QtGui
# from PyQt6.QtCore import Qt

from singleton_decorator import singleton

NOTE_HEAD = "𝅘 "
WHOLE_NOTE = "𝅝 "
HALF_NOTE = "𝅗𝅥 "
QUATER_NOTE = "𝅘𝅥 "
EIGTH_NOTE = "𝅘𝅥𝅮 "
EIGHT_NOTE = "𝅘𝅥𝅮 "
SIXTEENTH_NOTE = "𝅘𝅥𝅯 "
THRITYSEC_NOTE = "𝅘𝅥𝅰 "
SIXTYFORTH_NOTE = "𝅘𝅥𝅱 "
FLAT_SIGN = "♭ "
NATURAL_SIGN = "♮ "
SHARP_SIGN = "♯ "
UPSTROKE = "\u2191"
DOWNSTROKE = "\u2193"

BARLINE1 = "𝄀 "
BARLINE2 = "𝄁 "
END_REPEAT = "𝄂 "
START_REPEAT = "𝄃 "


TREBLE_CLEFF = "𝄞 "
DRUM_CLEFF = "𝄥 "
BASS_CLEFF = "𝄢 "
TENOR_CLEFF = "𝄡 "


WHOLE_REST = "𝄻 "
HALF_REST = "𝄼 "
QUATER_REST = "𝄽 "
EIGHTH_REST = "𝄾 "
SIXTEENTH_REST = "𝄿 "
THRITYSEC_REST = "𝅀 "
SIXTYFORTH_REST = "𝅁 "

GHOST_NOTEHEAD = "𝅃 "
DOUBLE_GHOST_NOTEHEAD = "𝅃 𝅃 "

FORTE_SYMBOL=u'\U0001D191'
MEZZO_SYMBOL=u'\U0001D190'
PIANO_SYMBOL=u'\U0001D18F'


BLACK_NOTEHEAD = u"\U0001D158"
VOID_NOTEHEAD = u"\U0001D157"



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
STAFF_LINE_SPACING = 16
STAFF_ACCENT_SPACING = 13
STAFF_NUMBER_OF_LINES = 5  # number of permenant lines
STAFF_TEXT_FONT_SIZE = 45
STAFF_ACCENT_FONT_SIZE = 20
STAFF_CHORD_STEM_X = 29
STAFF_TEXT_FONT = "DejaVu Sans" # Has music unicode symbols

ORNAMENT_MARKING_HEIGHT = 50



STAFF_HEIGHT = (STAFF_ABOVE_LINES + STAFF_BELOW_LINES + STAFF_NUMBER_OF_LINES)\
    * STAFF_LINE_SPACING
STAFF_SYM_WIDTH = 45
# clef + bpm + key
STAFF_HEADER_WIDTH = 200
STAFF_Y_START = 26 + (STAFF_ABOVE_LINES * STAFF_LINE_SPACING)





TABLATURE_NUM_LINES = 6
TABLATURE_LINE_SPACE = 15
TABLATURE_RECATNGLE_WIDTH = int(TABLATURE_LINE_SPACE/2)
TABLATURE_TEXT_SIZE = int(TABLATURE_LINE_SPACE/2)

Y_START = 26

E2_MIDI_CODE = 40
E6_MIDI_CODE = 88


@singleton
class TheYPositionMidiTable:
    """ Creates a lookup table that maps a Y coordinate to a midi note on
        a staff. 
    """

    def __init__(self):
        self.table = {}
        n = ['e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b', 'c', 'c#', 'd', 'd#']
        y_max = (1 + STAFF_ABOVE_LINES + STAFF_BELOW_LINES + STAFF_NUMBER_OF_LINES) \
            * STAFF_LINE_SPACING
        i = 0
        y = y_max
        for midi in range(E2_MIDI_CODE, E6_MIDI_CODE+1):
            note_name = n[i]
            i = (i+1) % len(n)
            self.table[midi] = y - STAFF_LINE_SPACING
            if len(note_name) == 1:
                y -= int(STAFF_LINE_SPACING/2)

    def get(self, k, defval):
        if k in self.table:
            return self.table[k]
        return defval


@singleton
class TheKeyMidiCodeTable:
    def __init__(self):

        def midicode_from_name(name):
            # starts at C1 which is midi code 24
            n = ['C', '', 'D', '', 'E', 'F', '', 'G', '', 'A', '', 'B']

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

        self.table = {
            "C": [],
            "C#": [midicode_from_name("F#5"),
                   midicode_from_name("C#5"),
                   midicode_from_name("G#5"),
                   midicode_from_name("D#5"),
                   midicode_from_name("A#4"),
                   midicode_from_name("E#5"),
                   midicode_from_name("B#4"),
                   ],
            "D": [
                midicode_from_name("F#5"),
                midicode_from_name("C#5")
            ],
            "A": [
                midicode_from_name("F#5"),
                midicode_from_name("C#5"),
                midicode_from_name("G#5")
            ],
            "E": [
                midicode_from_name("F#5"),
                midicode_from_name("C#5"),
                midicode_from_name("G#5"),
                midicode_from_name("D#5")
            ],
            "B": [
                midicode_from_name("F#5"),
                midicode_from_name("C#5"),
                midicode_from_name("G#5"),
                midicode_from_name("D#5"),
                midicode_from_name("A#4")
            ],
            "F": [
                midicode_from_name("Bb4")
            ],
            "Bb": [
                midicode_from_name("Bb4"),
                midicode_from_name("Eb5")
            ],
            "Eb": [
                midicode_from_name("Bb4"),
                midicode_from_name("Eb5"),
                midicode_from_name("Ab4")
            ]
        }

    def get(self, k, defval):
        if k in self.table:
            return self.table[k]
        return defval


# map the y position of the staff to a midi note.
YPositionMidiTable = TheYPositionMidiTable()
KeyMidiCodeTable = TheKeyMidiCodeTable()
