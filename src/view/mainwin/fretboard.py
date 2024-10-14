import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPolygon, QFont
from PyQt6.QtCore import Qt, QPoint

from view.config import GuitarFretboardStyle

class GuitarFretboard(QWidget):
    STRING_SPACING = 30
    START_X = 50
    END_X = 1000
    START_Y = 50

    def __init__(self):
        super().__init__()
        #self.setWindowTitle("Guitar Fretboard")
        self.setGeometry(100, 100, 1050, 250)  # Increased width to fit more frets
        self.tuning = []
        self.dots = []

    def setTuning(self, tuning):
        self.tuning = tuning

    def addDot(self, fret, string, rgb):
        self.dots.append((fret,string,QColor(*rgb)))

    def _draw_dots(self, painter: QPainter, fret_positions: list):
        for (fret, string, qp) in self.dots:
            x = fret_positions[fret]
            r = 20
            if fret > 0:
                x = int( (fret_positions[fret] + fret_positions[fret-1])/2 )
            y = self.START_Y + ((string-1) * self.STRING_SPACING)
             

            painter.setBrush(QBrush(qp, Qt.BrushStyle.SolidPattern))
            painter.drawEllipse(int(x) - 10, int(y) - 10, r, r)

    def _draw_tuning(self, painter: QPainter):
        text_color = QColor(*GuitarFretboardStyle.text_color_rgb)
        text_pen = QPen(text_color, 3)
        for (i,text) in enumerate(self.tuning):
            y = self.START_Y + (i * self.STRING_SPACING) + 2
            x = self.START_X - 40

            painter.setPen(text_pen)
            painter.drawText(x, y, text)


    def _draw_dot_using_current_pen(self, painter, start_y, string_spacing, fret_positions, fret, g_string):
        # Positioning the diamond
        fret_x = (fret_positions[fret-1] + fret_positions[fret]) / 2  # Midpoint of the 3rd fret
        string_y_lower = start_y + (g_string-1) * string_spacing  # Y position of 3rd string
        string_y = start_y + g_string * string_spacing  # Y position of 4th string
        diamond_center_y = (string_y_lower + string_y) / 2  # Center between 3rd and 4th string

        # Creating diamond points (rotated square) with a height of 7 pixels
        diamond_height = 7
        diamond_width = diamond_height  # Symmetric diamond (square rotated 45 degrees)
        points = [
            QPoint(int(fret_x), int(diamond_center_y - diamond_height / 2)),  # Top point
            QPoint(int(fret_x + diamond_width / 2), int(diamond_center_y)),   # Right point
            QPoint(int(fret_x), int(diamond_center_y + diamond_height / 2)),  # Bottom point
            QPoint(int(fret_x - diamond_width / 2), int(diamond_center_y))    # Left point
        ]
        diamond = QPolygon(points)
        painter.drawPolygon(diamond)

    def paintEvent(self, event):
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
        painter.fillRect(start_x, start_y - 10, end_x - start_x, fretboard_height, f_gb_color)


        fret_color = QColor(*GuitarFretboardStyle.fret_color_rgb)  # RGB for copper color
        fret_pen = QPen(fret_color, 5)

        text_color = QColor(*GuitarFretboardStyle.text_color_rgb)
        text_pen = QPen(text_color, 3)
        
        # Drawing the frets with decreasing spacing
        initial_fret_spacing = 50
        num_frets = 24
        start_y_fret = start_y - 10  # Start above the first string
        end_y_fret = start_y + (num_strings - 1) * string_spacing + 10  # End below the last string

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
            x += max(initial_fret_spacing - i, 5)  # Ensuring the spacing doesn't get too small



        # Drawing a gold circle between the 3rd and 4th strings on the 3rd fret
        orn_color = QColor(*GuitarFretboardStyle.orament_color_rgb)  # RGB for gold
        brush = QBrush(orn_color)
        painter.setBrush(brush)

        ornaments = [
            (3,3),
            (5,3),
            (7,3),
            (9,3),
            (12,2),
            (12,4),
            (15,3),
            (17,3),
            (19,3),
            (21,3)
        ]

        for (fret, g_str) in ornaments:
            self._draw_dot_using_current_pen(painter, start_y, string_spacing, fret_positions,\
                fret, g_str)

        string_color = QColor(*GuitarFretboardStyle.string_color_rgb) 
        for i in range(num_strings):
            y = start_y + i * string_spacing
            string_pen = QPen(string_color, i+3)
            painter.setPen(string_pen)    
            painter.drawLine(start_x, y, end_x, y)

        self._draw_tuning(painter)
        self._draw_dots(painter, fret_positions)


if __name__ == "__main__":
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
    window.addDot(12,1,(0,255,255))
    window.show()
    sys.exit(app.exec())
