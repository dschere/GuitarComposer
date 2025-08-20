import logging
from view.editor.glyphs.common import (STAFF_SYM_WIDTH, STAFF_HEIGHT,
    STAFF_HEADER_WIDTH, STAFF_LINE_SPACING, STAFF_ABOVE_LINES, QUATER_NOTE, TREBLE_CLEFF,
    SymFontSize, KeyMidiCodeTable, SHARP_SIGN, FLAT_SIGN, STAFF_NUMBER_OF_LINES,
    BARLINE2, BARLINE1, START_REPEAT,
    END_REPEAT
    )

from view.editor.glyphs.canvas import Canvas
from models.track import TabEvent, Track
from models.measure import Measure, TimeSig
from view.editor.glyphs.note_renderer import note_renderer
from util.midi import midi_codes
from view.events import Signals, EditorEvent 
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QSpinBox

class StaffMeasureBarlines(Canvas):
    START_OF_STAFF = 0
    END_MEASURE = 1
    BEGIN_REPEAT = 2
    END_REPEAT = 3
    END_BEGIN_NEW_REPEAT = 4

    def __init__(self, measure: int, mtype : int, width=STAFF_SYM_WIDTH, height=STAFF_HEIGHT):
        super().__init__(width, height)
        self.measure = measure
        self.mtype = mtype

    def mousePressEvent(self, _):
        if self.measure != -1:
            e = EditorEvent()
            e.ev_type = EditorEvent.MEASURE_CLICKED
            e.measure = self.measure
            Signals.editor_event.emit(e)
        
    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)
        text = BARLINE2
        
        if self.mtype == self.END_MEASURE:
            text = BARLINE1
        elif self.mtype == self.BEGIN_REPEAT:
            text = START_REPEAT  
        elif self.mtype == self.END_REPEAT:
            text = END_REPEAT     

        x=7
        size = ((STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING)
        top_line = STAFF_ABOVE_LINES * STAFF_LINE_SPACING
        bottom_line = top_line + (STAFF_NUMBER_OF_LINES-1) * STAFF_LINE_SPACING
        if self.measure != -1:
            self.draw_symbol(painter, str(self.measure), x=5, 
                y=top_line-10, draw_lines=False, size=12 )         
        self.draw_symbol(painter, text, x=x, y=bottom_line, size=size)

        


class StaffGlyph(Canvas):
    def __init__(self, te : TabEvent, m: Measure, track: Track):
        super().__init__(STAFF_SYM_WIDTH, STAFF_HEIGHT)
        self.te = te
        self.m = m
        self.track_model = track
        if m.key in ['F','Bb','Eb','Ab','Db','Gb']:
            self.accent = FLAT_SIGN
        else:
            self.accent = SHARP_SIGN
        (ts, bpm, key, cleff) = track.getMeasureParams(m)
        self.cleff = cleff
        self.play_line = False

    def _draw_play_line(self, painter):
        # STAFF_SYM_WIDTH, STAFF_HEIGHT
        saved_pen = painter.pen()
        painter.setPen(QPen(Qt.GlobalColor.red, 3, Qt.PenStyle.DashLine))
                    
        x = int(STAFF_SYM_WIDTH / 2)  # Center of the widget
        painter.drawLine(x, 0, x, STAFF_HEIGHT)    
        painter.setPen(saved_pen)  

    def set_play_line(self):
        self.play_line = True    
        

    def clear_play_line(self):
        self.play_line = False
        
        
    def _get_renderer(self):
        tc : TabEvent = self.te
        m : Measure = self.m
        dot_count = int(tc.dotted) + int(tc.double_dotted)
        
        return note_renderer(self.cleff, dot_count)

    def _render_note(self, painter):
        r : note_renderer = self._get_renderer()
        te : TabEvent = self.te

        # find note
        for (gstring,fret) in enumerate(te.fret):
            if fret != -1:
                tuning = self.track_model.tuning
                base_midi_code = tuning[gstring]
                midi_code = midi_codes.midi_code(base_midi_code) + fret
                y = r.draw_note(painter, midi_code, self.accent, te.duration)
                te.note_ypos[gstring] = y
                break

    def _render_chord(self, painter):
        r : note_renderer = self._get_renderer()
        te : TabEvent = self.te
        # collect and and sort midi codes
        midi_code_collection = set()
        for (gstring,fret) in enumerate(te.fret):
            if fret != -1:
                tuning = self.track_model.tuning
                base_midi_code = tuning[gstring]
                midi_code = midi_codes.midi_code(base_midi_code) + fret
                y = r.get_y_coord(midi_code, self.accent)
                te.note_ypos[gstring] = y 

                midi_code_collection.add(midi_code)
        midi_list = sorted(list(midi_code_collection))

        # draw note heads
        for midi_code in midi_list:
            r.draw_notehead(painter, midi_code, self.accent, te.duration)
             
        # if duration quarter or smaller draw connecting line.
        # the greated midi note is drawn as a quarter note with its staff 
        if te.duration != 4.0:
            r.draw_stem_line(painter, midi_list, self.accent)        
            r.draw_note(painter, midi_list[-1], self.accent, te.duration)    


    def _render_rest(self, painter):
        r : note_renderer = self._get_renderer()
        tc : TabEvent = self.te
        r.draw_rest(painter, tc.duration)
        

    def canvas_paint_event(self, painter):
        self.draw_staff_background(painter)

        if self.play_line:
            self._draw_play_line(painter) 

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
        if self.staff_bpm:
            bpm = self.staff_bpm
            self.draw_symbol(painter, f"{QUATER_NOTE} = {bpm}",
                size=12, draw_lines=False, x=0, y=y)

        # draw staff
        if self.staff_symbol:
            cleff_y_pos = STAFF_LINE_SPACING * \
                STAFF_ABOVE_LINES+SymFontSize[self.staff_symbol]
            self.draw_symbol(painter, self.staff_symbol, y=cleff_y_pos)

        # draw time signature
        if self.staff_timesig:
            x : TimeSig = self.staff_timesig
            ts = [f'{x.beats_per_measure}',f'{x.beat_note_id}']
            
            num_y = (STAFF_ABOVE_LINES * STAFF_LINE_SPACING) + 24
            den_y = num_y + (STAFF_LINE_SPACING * 2) + 8
            self.draw_symbol(painter, ts[0], x=60, y=num_y)
            self.draw_symbol(painter, ts[1], x=60, y=den_y)

        # draw accents (sharps and flat) based on the key
        if self.staff_key:
            x = 100 # type: ignore
            key_codes = KeyMidiCodeTable.get(self.staff_key, [])

            sign = SHARP_SIGN
            if 'b' in self.staff_key or self.staff_key == 'F':
                sign = FLAT_SIGN
            for midi_code in key_codes:
                self.draw_sign(painter, sign, x, midi_code)
                x += 10 # type: ignore

