import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QFont, QPen


NOTE_HEAD = "𝅘 "
WHOLE_NOTE = "𝅝 "
HALF_NOTE = "𝅗𝅥 "
QUATER_NOTE = "𝅘𝅥 "
EIGHT_NOTE = "𝅘𝅥𝅮 "
SIXTEENTH_NOTE = "𝅘𝅥𝅯 "
THRITYSEC_NOTE = "𝅘𝅥𝅰 "
SIXTYFORTH_NOTE = "𝅘𝅥𝅱 "

note_text = [
    NOTE_HEAD,
    WHOLE_NOTE,
    HALF_NOTE,
    QUATER_NOTE,
    EIGHT_NOTE,
    SIXTEENTH_NOTE,
    THRITYSEC_NOTE,
    SIXTYFORTH_NOTE
]

class GridExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Grid Example")
        self.setGeometry(100, 100, 1000, 1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cell_size = 30

        # Set font for text
        font = QFont("DejaVu Sans", int(cell_size*1.5))
        painter.setFont(font)


        painter.begin(self)

        # Draw grid
        for i in range(cell_size):
            for j in range(cell_size):
                x = i * cell_size
                y = j * cell_size
                painter.drawRect(x, y, cell_size, cell_size)

        # Draw text at position (10, 10)

        
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        
        # draw 16 notes (minus accents)
        for x in range(16):
            t = note_text[x % len(note_text)]
            y = int(cell_size/2 * x + cell_size*0.12) + cell_size
            painter.drawText(cell_size*x,y, t)
            stem_len = int(cell_size)            
            stem_x = int(cell_size*x + (cell_size/2)) + 1
            stem_offset = int(cell_size/7) 
            painter.drawLine(stem_x, y-stem_offset, stem_x, y-stem_len-stem_offset)

        painter.end() 
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridExample()
    window.show()
    sys.exit(app.exec())

