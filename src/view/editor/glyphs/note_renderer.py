from PyQt6 import QtGui
from PyQt6.QtCore import Qt

from view.editor.glyphs.common import (BASS_CLEFF, BLACK_NOTEHEAD, DRUM_CLEFF, 
    EIGHTH_REST, EIGTH_NOTE, HALF_NOTE, HALF_REST, QUATER_NOTE, QUATER_REST, SIXTEENTH_NOTE, 
    SIXTEENTH_REST, SIXTYFORTH_NOTE, SIXTYFORTH_REST, STAFF_CHORD_STEM_X, STAFF_NUMBER_OF_LINES, STAFF_TEXT_FONT, 
    STAFF_TEXT_FONT_SIZE, STAFF_Y_START, STAFF_LINE_SPACING, SHARP_SIGN, THRITYSEC_NOTE, 
    THRITYSEC_REST, TREBLE_CLEFF, VOID_NOTEHEAD, WHOLE_NOTE, WHOLE_REST,
    STAFF_ACCENT_SPACING, STAFF_ACCENT_FONT_SIZE, STAFF_ABOVE_LINES, TENOR_CLEFF)
from music import durationtypes as DT




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
    y_space = 7 # number of y positions not coordinates
    midi_g5 = 91
    midi_g5_octave_offset = (y_space * (int(midi_g5 / 12) - 2))
    sharp_offset = midi_g5_octave_offset + sharp_seq[midi_g5 % 12]
    flat_offset = midi_g5_octave_offset + flat_seq[midi_g5 % 12]

    for midi in range(24, 128):
        octave = int(midi / 12) - 2
        n_s = sharp_seq[midi % 12] + (y_space * octave)
        n_f = flat_seq[midi % 12] + (y_space * octave)

        sharp_step_table[midi] = sharp_offset - n_s
        flat_step_table[midi] = flat_offset - n_f

    def test_pattern(self, painter):
        from util.midi import midi_codes
        font = QtGui.QFont(STAFF_TEXT_FONT, 6)
        painter.setFont(font)
        for (midi, offset) in self.sharp_step_table.items():
            line_spacing = STAFF_LINE_SPACING
            inc = int(line_spacing/2)
            text = midi_codes.name(midi, '#')
            painter.drawText(0, offset * inc, text)

    def __init__(self, cleff, dot_count=0):
        self.cleff = cleff
        self.dot_count = dot_count

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
            DT.EIGHT: EIGTH_NOTE,
            DT.SIXTEENTH: SIXTEENTH_NOTE,
            DT.THIRTYSECOND: THRITYSEC_NOTE,
            DT.SIXTYFORTH: SIXTYFORTH_NOTE
        }[dtype] + ("." * self.dot_count)

    def get_rest_text(self, dtype):
        return {
            DT.WHOLE: WHOLE_REST,
            DT.HALF: HALF_REST,
            DT.QUARTER: QUATER_REST,
            DT.EIGHT: EIGHTH_REST,
            DT.SIXTEENTH: SIXTEENTH_REST,
            DT.THIRTYSECOND: THRITYSEC_REST,
            DT.SIXTYFORTH: SIXTYFORTH_REST
        }[dtype] + ('.' * self.dot_count)

    def get_y_coord(self, midi_code, accent):
        # global sharp_step_table, flat_step_table

        line_spacing = STAFF_LINE_SPACING
        y_start = STAFF_Y_START - 7
        inc = int(line_spacing/2)
        offset = inc*STAFF_ABOVE_LINES

        # adjust y_start based on cleff
        y_start -= {
            TREBLE_CLEFF: 0,
            DRUM_CLEFF: 0,
            BASS_CLEFF: line_spacing * 6,
            TENOR_CLEFF: line_spacing * 4
        }[self.cleff]

        if accent == SHARP_SIGN:
            return int(offset + (self.sharp_step_table[midi_code] * inc))
        else:
            return int(offset + (self.flat_step_table[midi_code] * inc))

    def draw_note_accent(self, painter, conf, midi_code, accent, x):
        y = self.get_y_coord(midi_code, accent)

        # do we need to render a # or b infront of the note?
        if accent_table[midi_code % 12]:

            # size = conf.line_spacing
            accent_font_size = conf.accent_font_size
            # text_font_size = conf.text_font_size
            text_font = conf.text_font

            font = QtGui.QFont(text_font, accent_font_size)
            painter.setFont(font)

            # draw a sharp or flat sign next to the note head
            painter.drawText(x, y+10, accent)

    def draw_rest(self, painter, dtype):
        y = self.get_y_coord(67, SHARP_SIGN)
        x = STAFF_ACCENT_SPACING
        text = self.get_rest_text(dtype)
        font = QtGui.QFont(STAFF_TEXT_FONT, STAFF_TEXT_FONT_SIZE)
        painter.setFont(font)
        if dtype == DT.WHOLE:
            y -= 8
        elif dtype == DT.HALF:
            y -= 1
        painter.drawText(x, y, text)

    def draw_note(self, painter, midi_code, accent, dtype, note_head=False):
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in
        # different staff positions depending on which it is.
        accent_spacing = STAFF_ACCENT_SPACING
        text_font_size = STAFF_TEXT_FONT_SIZE
        text_font = STAFF_TEXT_FONT

        y = self.get_y_coord(midi_code, accent)
        # do we need to render a # or b infront of the note?
        if accent_table[midi_code % 12]:
            accent_font_size = STAFF_ACCENT_FONT_SIZE

            font = QtGui.QFont(text_font, accent_font_size)
            painter.setFont(font)

            # draw a sharp or flat sign next to the note head
            painter.drawText(0, y+3, accent)

        font = QtGui.QFont(text_font, text_font_size)
        painter.setFont(font)

        if note_head:
            text = self.get_note_head_text(dtype)
        else:
            text = self.get_tail_note_text(dtype)
        painter.drawText(accent_spacing, y-3, text)

        # draw ledger lines above/below staff as needed
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING
        x = 10
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


    def draw_notehead(self, painter, midi_code, accent, dtype):
        # Note: accent is used because we need to know if we are
        # rendering sharps or flats since the same note can be in
        # different staff positions depending on which it is.
        # line_spacing = conf.line_spacing
        self.draw_note(painter, midi_code, accent, dtype, True)

    def draw_stem_line(self, painter, midi_code_list, accent):
        # draw a line connecting the notes is dtype is not
        # a whole or half note.
        stem_x = STAFF_CHORD_STEM_X

        low_y = self.get_y_coord(midi_code_list[0], accent)
        high_y = self.get_y_coord(midi_code_list[-1], accent)

        notehead_offset = int(STAFF_TEXT_FONT_SIZE/7)
        painter.drawLine(
            stem_x, low_y - notehead_offset,
            stem_x, high_y - notehead_offset)


    