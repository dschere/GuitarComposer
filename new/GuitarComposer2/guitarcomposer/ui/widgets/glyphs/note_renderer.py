from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from .constants import *
from guitarcomposer.common import durationtypes as DT


per_octave_names = ['C', 'C#/Db', 'D', 'D#/Eb', 'E',
                    'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
accent_table = [False, True, False, True, False,
                False, True, False, True, False, True, False]

# generate two tables depending if we are used sharps or flats.
# this lookup table precomputes the number of pixels (in line_spacings)
# the note shall be rendered. Note an A# and Gb are the same note but
# drawn on a different y position on the staff, the values are computed
# from the G5 note which is the y_start position on the first line of
# the staff.

class note_renderer:
    sharp_step_table, flat_step_table = {}, {}

    # from C -> B count the y offset changes
    sharp_seq = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
    flat_seq = [0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6]

    midi_g5 = 91
    midi_g5_octave_offset = (7 * (int(midi_g5 / 12) - 2))
    sharp_offset = midi_g5_octave_offset + sharp_seq[midi_g5 % 12]
    flat_offset = midi_g5_octave_offset + flat_seq[midi_g5 % 12]

    for midi in range(24, 128):
        octave = int(midi / 12) - 2
        n_s = sharp_seq[midi % 12] + (7 * octave)
        n_f = flat_seq[midi % 12] + (7 * octave)

        sharp_step_table[midi] = sharp_offset - n_s
        flat_step_table[midi] = flat_offset - n_f
    

    def __init__(self, cleff):
        self.cleff = cleff

    def get_note_head_text(self, dtype):
        return {
            DT.WHOLE: VOID_NOTEHEAD,
            DT.HALF: VOID_NOTEHEAD
        }.get(dtype, BLACK_NOTEHEAD)

    def get_tail_note_text(self, dtype):
        return {
            DT.WHOLE: WHOLE_NOTE,
            DT.HALF: HALF_NOTE,
            DT.QUARTER: QUATER_NOTE,
            DT.EIGHT: EIGHT_NOTE,
            DT.SIXTEENTH: SIXTEENTH_NOTE,
            DT.THIRTYSECOND: THRITYSEC_NOTE,
            DT.SIXTYFORTH: SIXTYFORTH_NOTE
        }[dtype]

    def get_y_coord(self, midi_code, conf, accent):
        #global sharp_step_table, flat_step_table

        line_spacing = conf.line_spacing
        y_start = conf.y_start - 10
        inc = line_spacing/2

        # adjust y_start based on cleff
        y_start -= {
            TREBLE_CLEFF: 0,
            DRUM_CLEFF: 0,
            BASS_CLEFF: line_spacing * 6,
            TENOR_CLEFF: line_spacing * 4
        }[self.cleff]

        if accent == SHARP_SIGN:
            return int(y_start + (self.sharp_step_table[midi_code] * inc))
        else:
            return int(y_start + (self.flat_step_table[midi_code] * inc))

    def draw_note_accent(self, painter, conf, midi_code, accent, x):
        y = self.get_y_coord(midi_code, conf, accent)
        # do we need to render a # or b infront of the note?
        if accent_table[midi_code % 12]:

            size = conf.line_spacing
            accent_font_size = conf.accent_font_size
            text_font_size = conf.text_font_size
            text_font = conf.text_font

            font = QtGui.QFont(text_font, accent_font_size)
            painter.setFont(font)

            # draw a sharp or flat sign next to the note head
            painter.drawText(x, y+10, accent)


    def draw_note(self, painter, conf, midi_code, accent, dtype):
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in
        # different staff positions depending on which it is.
        line_spacing = conf.line_spacing
        accent_spacing = conf.accent_spacing

        y = self.get_y_coord(midi_code, conf, accent)
        # do we need to render a # or b infront of the note?
        if accent_table[midi_code % 12]:

            size = conf.line_spacing
            accent_font_size = conf.accent_font_size
            text_font_size = conf.text_font_size
            text_font = conf.text_font

            font = QtGui.QFont(text_font, accent_font_size)
            painter.setFont(font)

            # draw a sharp or flat sign next to the note head
            painter.drawText(0, y+3, accent)

            size = conf.line_spacing
            font = QtGui.QFont(text_font, text_font_size)
            painter.setFont(font)

        text = self.get_tail_note_text(dtype)
        painter.drawText(accent_spacing, y, text)

    def draw_notehead(self, painter, conf, midi_code, accent, dtype):
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in
        # different staff positions depending on which it is.
        line_spacing = conf.line_spacing
        accent_spacing = conf.accent_spacing

        y = self.get_y_coord(midi_code, conf, accent)
        text = self.get_note_head_text(dtype)
        painter.drawText(accent_spacing, y, text)
