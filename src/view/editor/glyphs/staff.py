from view.editor.glyphs.common import (STAFF_SYM_WIDTH, STAFF_HEIGHT,
                                       STAFF_HEADER_WIDTH, STAFF_LINE_SPACING, STAFF_ABOVE_LINES, QUATER_NOTE, TREBLE_CLEFF,
                                       SymFontSize, KeyMidiCodeTable, SHARP_SIGN, FLAT_SIGN, STAFF_NUMBER_OF_LINES,
                                       BARLINE2, BARLINE1, START_REPEAT,
    END_REPEAT
                                       )

from view.editor.glyphs.canvas import Canvas
from models.track import StaffEvent, TabEvent, Track
from view.editor.glyphs.note_renderer import note_renderer
from src.util.midi import midi_codes
from view.events import Signals, EditorEvent 

class StaffMeasureBarlines(Canvas):
    START_OF_STAFF = 0
    END_MEASURE = 1
    BEGIN_REPEAT = 2
    END_REPEAT = 3


    def __init__(self, measure: int, mtype : int, repeat_count : int = 1):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT)
        self.measure = measure
        self.mtype = mtype
        self.repeat_count = repeat_count

    def mousePressEvent(self, event):
        e = EditorEvent()
        e.ev_type = EditorEvent.MEASURE_CLICKED
        e.measure = self.measure
        Signals.editor_event.emit(e)
        
        
    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)
        text = BARLINE2
        repeat_text = None

        if self.mtype == self.END_MEASURE:
            text = BARLINE1
        elif self.mtype == self.BEGIN_REPEAT:
            text = START_REPEAT  
        elif self.mtype == self.END_REPEAT:
            text = END_REPEAT
            repeat_text = str(self.repeat_count)     

        x=7
        size = ((STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING)
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING
        self.draw_symbol(painter, str(self.measure), x=5, 
            y=top_line-10, draw_lines=False, size=12 )         
        self.draw_symbol(painter, text, x=x, y=bottom_line, size=size)

        if repeat_text:
            self.draw_symbol(painter, str(self.repeat_count),
                x=x, y=bottom_line+13, size=12, bold=True, 
                draw_lines=False)
        


class StaffGlyph(Canvas):
    def __init__(self, te : TabEvent):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT)
        self.te = te
        self.se = StaffEvent()
        self.accent = SHARP_SIGN
        self.tuning = Track().tuning

    def setup(self, se: StaffEvent, te: TabEvent, tuning):
        self.te = te
        self.se = se
        self.tuning = tuning

        if se.key in ['F','Bb','Eb','Ab','Db','Gb']:
            self.accent = FLAT_SIGN
        else:
            self.accent = SHARP_SIGN
        # schedule a refresh
        self.update()  

    def _get_renderer(self):
        tc : TabEvent = self.te
        se : StaffEvent = self.se
        dot_count = int(tc.dotted) + int(tc.double_dotted)
        cleff = se.cleff
        return note_renderer(cleff, dot_count)

    def _render_note(self, painter):
        r : note_renderer = self._get_renderer()
        tc : TabEvent = self.te
        se : StaffEvent = self.se

        # find note
        for (gstring,fret) in enumerate(tc.fret):
            if fret != -1:
                base_midi_code = self.tuning[gstring]
                midi_code = midi_codes.midi_code(base_midi_code) + fret
                r.draw_note(painter, midi_code, self.accent, tc.note_duration)
                break

    def _render_chord(self, painter):
        r : note_renderer = self._get_renderer()
        tc : TabEvent = self.te
        # collect and and sort midi codes
        midi_code_collection = set()
        for (gstring,fret) in enumerate(tc.fret):
            if fret != -1:
                base_midi_code = self.tuning[gstring]
                midi_code = midi_codes.midi_code(base_midi_code) + fret
                midi_code_collection.add(midi_code)
        midi_list = sorted(list(midi_code_collection))

        # draw note heads
        for midi_code in midi_list:
            r.draw_notehead(painter, midi_code, self.accent, tc.note_duration)

        # if duration quarter or smaller draw connecting line.
        # the greated midi note is drawn as a quarter note with its staff 
        if tc.note_duration != 4.0:
            r.draw_stem_line(painter, midi_list, self.accent)        
            r.draw_note(painter, midi_list[-1], self.accent, tc.note_duration)    


    def _render_rest(self, painter):
        r : note_renderer = self._get_renderer()
        tc : TabEvent = self.te
        r.draw_rest(painter, tc.note_duration)
        

    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)

        # determine if this is a note, a chord or a rest.
        {
            self.te.REST: self._render_rest,
            self.te.NOTE: self._render_note,
            self.te.CHORD: self._render_chord
        }[self.te.classify()](painter)


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
        key_codes = KeyMidiCodeTable.get(self.staff_key, [])

        sign = SHARP_SIGN
        if 'b' in self.staff_key or self.staff_key == 'F':
            sign = FLAT_SIGN
        for midi_code in key_codes:
            self.draw_sign(painter, sign, x, midi_code)
            x += 10

        # draw the two verticle lines that mark the end of the
        # the staff header
        # x += 7
        # size = ((STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING)
        # top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        # bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING
        # self.draw_symbol(painter, BARLINE2, x=x, y=bottom_line, size=size)
