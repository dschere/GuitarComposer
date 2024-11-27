import sys

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import (QPainter, QPen, QColor, QBrush,
                         QPolygon, QFont, QMouseEvent)
from PyQt6.QtCore import Qt, QPoint

from view.config import GuitarFretboardStyle
from util.midi import midi_codes
from util.coordinateMap import CoordinateMap

from view.events import EditorEvent, Signals, ScaleSelectedEvent

from models.note import Note


class GuitarFretboard(QWidget):
    STRING_SPACING = 30
    START_X = 50
    END_X = 1000
    START_Y = 50

    def _init_coordinate_map(self, fret_positions, string_positions):
        self.cm = CoordinateMap(
            self.START_X-10,
            self.START_Y-10,
            self.END_X+10,
            self.START_Y + (len(self.tuning) * self.STRING_SPACING) + 10)
        for (string, string_y_pos) in enumerate(string_positions):
            start_midi = midi_codes.midi_code(self.tuning[string])
            for (fret, fret_x_pos) in enumerate(fret_positions):
                n = Note()
                n.midi_code = start_midi + fret
                n.fret = fret
                n.string = string
                n.velocity = 80
                self.cm.add(fret_x_pos, string_y_pos, n)

    def _update_active_notes(self, n: Note):
        fret_playing = self.string_playing_fret[n.string]
        if fret_playing != -1:
            self.removeDot(fret_playing, n.string)
        if n.is_playing:
            self.addDot(n.fret, n.string, GuitarFretboardStyle.note_press)
            self.string_playing_fret[n.string] = n.fret
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            y = event.position().y()
            n = self.cm.match(x, y)
            if n:
                # Toggle state
                n.is_playing = not n.is_playing
                if n.is_playing:
                    n.rest = False
                    playing_note = self.string_playing_note[n.string]
                    if playing_note:
                        Signals.preview_stop.emit(playing_note)
                        self.string_playing_note[n.string] = n
                    Signals.preview_play.emit(n)
                else:
                    n.rest = True
                    Signals.preview_stop.emit(n)
                    self.string_playing_note[n.string] = None
                self._update_active_notes(n)

    def editor_event(self, evt: EditorEvent):
        if evt.ev_type == EditorEvent.ADD_MODEL:
            if evt.model:
                self.tuning = evt.model.tuning
                self.update()
        elif evt.ev_type == EditorEvent.TUNING_CHANGE:
            if evt.tuning:
                self.tuning = evt.tuning
                self.update()

    def __init__(self):
        super().__init__()

        # Increased width to fit more frets
        self.scale_note_tooltip = {}
        self.setGeometry(100, 100, 1025, 250)
        self.setFixedHeight(250)
        self.setFixedWidth(1025)
        self.tuning = [
            "E4",
            "B3",
            "G3",
            "D3",
            "A2",
            "E2"
        ]
        # keep track of strings playing notes, only one allowed per string
        self.string_playing_fret = [-1 for i in range(len(self.tuning))]
        self.string_playing_note = [None for i in range(len(self.tuning))]
        self.dots = {}
        self.scale = []
        self.scale_seq = None
        self.cm = None
        self.degrees = None

        Signals.scale_selected.connect(self.on_scale_selected)
        Signals.clear_scale.connect(self.on_clear_scale_overlay)
        Signals.editor_event.connect(self.editor_event)

    def on_scale_selected(self, evt: ScaleSelectedEvent):
        self.setScale(evt.scale_midi, evt.scale_seq)
        self.degrees = evt.degrees
        self.update()

    def on_clear_scale_overlay(self):
        self.scale = []
        self.update()

    def setScale(self, scale, scale_seq):
        self.scale = scale
        self.scale_seq = scale_seq

    def setTuning(self, tuning):
        self.tuning = tuning

    def addDot(self, fret, string, rgb):
        self.dots[(fret, string)] = QColor(*rgb)

    def removeDot(self, fret, string):
        k = (fret, string)
        if k in self.dots:
            del self.dots[k]


    def _render_scale(self, painter: QPainter, fret_positions: list):
        if len(self.scale) == 0:
            return  # nothing to render

        mc_ranges_per_string = []
        for (string, text) in enumerate(self.tuning):
            y = self.START_Y + (string * self.STRING_SPACING)
            start_mc = midi_codes.midi_code(text)
            end_mc = start_mc + 24
            mc_ranges_per_string.append((y, start_mc, end_mc))

        def_scale_color = QColor(*GuitarFretboardStyle.scale_color_rgb)
        root_color = QColor(*GuitarFretboardStyle.scale_root_color_rgb)
        for (i, midi_code) in enumerate(self.scale):
            steps = self.scale_seq[i % len(self.scale_seq)]
            if steps == 1:
                color = root_color
            else:
                color = def_scale_color

            for (y, start_mc, end_mc) in mc_ranges_per_string:
                if midi_code >= start_mc and midi_code <= end_mc:
                    fret = midi_code - start_mc
                    x = fret_positions[fret]

                    # enlarge cricles if there is degree text
                    r = 23
                    p = 13
                    if not self.degrees:
                        r = 20
                        p = 10

                    painter.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
                    painter.drawEllipse(int(x) - p, int(y) - p, r, r)

                    if self.degrees:
                        text = self.degrees[i % len(self.degrees)]
                        x_pos = int(x) - 5
                        if len(text) > 1:
                            x_pos -= 3
                        painter.drawText(x_pos, int(y) + 5, text)


    def _draw_dots(self, painter: QPainter, fret_positions: list):
        for ((fret, string), qp) in self.dots.items():
            x = fret_positions[fret]
            r = 20
            if fret > 0:
                # x = int( (fret_positions[fret] + fret_positions[fret-1])/2 )
                x = fret_positions[fret]
            y = self.START_Y + (string * self.STRING_SPACING)

            painter.setBrush(QBrush(qp, Qt.BrushStyle.SolidPattern))
            painter.drawEllipse(int(x) - 10, int(y) - 10, r, r)

    def _draw_tuning(self, painter: QPainter):
        text_color = QColor(*GuitarFretboardStyle.text_color_rgb)
        text_pen = QPen(text_color, 3)
        for (i, text) in enumerate(self.tuning):
            y = self.START_Y + (i * self.STRING_SPACING) + 2
            x = self.START_X - 40

            painter.setPen(text_pen)
            painter.drawText(x, y, text)

    def _draw_dot_using_current_pen(self, painter,
                                    start_y, string_spacing,
                                    fret_positions,
                                    fret, g_string):
        # Positioning the diamond
        # Midpoint of the 3rd fret
        fret_x = (fret_positions[fret-1] + fret_positions[fret]) / 2
        string_y_lower = start_y + (g_string-1) * \
            string_spacing  # Y position of 3rd string
        # Y position of 4th string
        string_y = start_y + g_string * string_spacing
        diamond_center_y = (string_y_lower + string_y) / \
            2  # Center between 3rd and 4th string

        # Creating diamond points (rotated square) with a height of 7 pixels
        diamond_height = 7
        # Symmetric diamond (square rotated 45 degrees)
        diamond_width = diamond_height
        points = [
            QPoint(int(fret_x), int(diamond_center_y -
                   diamond_height / 2)),  # Top point
            QPoint(int(fret_x + diamond_width / 2),
                   int(diamond_center_y)),   # Right point
            QPoint(int(fret_x), int(diamond_center_y +
                   diamond_height / 2)),  # Bottom point
            QPoint(int(fret_x - diamond_width / 2),
                   int(diamond_center_y))    # Left point
        ]
        diamond = QPolygon(points)
        painter.drawPolygon(diamond)

    def paintEvent(self, event):
        self.scale_note_tooltip = {}
        painter = QPainter(self)

        bg_color = QColor(*GuitarFretboardStyle.background_color_rgb)
        painter.fillRect(self.rect(), bg_color)

        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        # Drawing the strings (horizontal lines)
        string_spacing = self.STRING_SPACING
        num_strings = 6
        start_x = self.START_X
        end_x = self.END_X  # Increased to accommodate more frets
        start_y = self.START_Y
        fretboard_height = ((num_strings - 1) * string_spacing) + 20

        f_gb_color = QColor(*GuitarFretboardStyle.fretboard_bg_color_rgb)
        painter.fillRect(start_x, start_y - 10, end_x -
                         start_x, fretboard_height, f_gb_color)

        # RGB for copper color
        fret_color = QColor(*GuitarFretboardStyle.fret_color_rgb)
        fret_pen = QPen(fret_color, 5)

        text_color = QColor(*GuitarFretboardStyle.text_color_rgb)
        text_pen = QPen(text_color, 3)

        # Drawing the frets with decreasing spacing
        initial_fret_spacing = 50
        num_frets = 24
        start_y_fret = start_y - 10  # Start above the first string
        end_y_fret = start_y + (num_strings - 1) * \
            string_spacing + 10  # End below the last string

        copperplate_font = QFont("Copperplate", 12)
        painter.setFont(copperplate_font)

        x = start_x
        fret_positions = []
        for i in range(num_frets + 1):  # +1 to draw the nut and last fret
            painter.setPen(fret_pen)
            painter.drawLine(x, start_y_fret, x, end_y_fret)
            fret_positions.append(x)
            painter.setPen(text_pen)
            painter.drawText(x-5, end_y_fret+17, str(i))

            # Decrease spacing for the next fret by 1 pixel
            # Ensuring the spacing doesn't get too small
            x += max(initial_fret_spacing - i, 5)

        # Drawing a gold circle between the 3rd and 4th strings on the 3rd fret
        orn_color = QColor(
            *GuitarFretboardStyle.orament_color_rgb)  # RGB for gold
        brush = QBrush(orn_color)
        painter.setBrush(brush)

        ornaments = [
            (3, 3),
            (5, 3),
            (7, 3),
            (9, 3),
            (12, 2),
            (12, 4),
            (15, 3),
            (17, 3),
            (19, 3),
            (21, 3)
        ]

        for (fret, g_str) in ornaments:
            self._draw_dot_using_current_pen(painter, start_y,
                                             string_spacing,
                                             fret_positions,
                                             fret, g_str)

        string_color = QColor(*GuitarFretboardStyle.string_color_rgb)
        string_positions = []
        for i in range(num_strings):
            y = start_y + i * string_spacing
            string_positions.append(y)
            string_pen = QPen(string_color, i+3)
            painter.setPen(string_pen)
            painter.drawLine(start_x, y, end_x, y)

        self._draw_tuning(painter)
        self._render_scale(painter, fret_positions)
        self._draw_dots(painter, fret_positions)
        if not self.cm:
            self._init_coordinate_map(fret_positions, string_positions)


if __name__ == "__main__":
    from util.scale import MusicScales

    app = QApplication(sys.argv)
    window = GuitarFretboard()

    tuning = [
        "E4",
        "B3",
        "G3",
        "D3",
        "A2",
        "E2"
    ]
    window.setTuning(tuning)
    ms = MusicScales()
    scale, scale_seq = ms.generate_midi_scale_codes("Major Scale", "C")
    window.setScale(scale, scale_seq)
    window.addDot(12, 1, (0, 255, 0))

    def handle_play(n: Note):
        print("preview_play " + str(vars(n)))

    def handle_stop(n: Note):
        print("preview_stop " + str(vars(n)))

    Signals.preview_play.connect(handle_play)
    Signals.preview_stop.connect(handle_stop)

    window.show()
    sys.exit(app.exec())
