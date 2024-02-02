"""

Draws tablature like this

-----
-----
-----
---2-
--2--
-0---

Hovering over is a little square cursor that directs key events 
to render text

"""


from PyQt6.QtGui import QPainter, QPen, QColor


"""
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor
import sys

class HorizontalLinesWidget(QWidget):
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.begin(self)
        self.draw_lines(qp)
        qp.end()

    def draw_lines(self, qp):
        # Define some parameters
        line_color = QColor(0, 0, 0)  # Black color
        line_height = self.height() // 7  # Divide the widget height by 7 to get 6 equal lines
        y = line_height

        # Draw 6 horizontal lines
        for _ in range(6):
            qp.setPen(line_color)
            qp.drawLine(0, y, self.width(), y)
            y += line_height

def main():
    app = QApplication(sys.argv)
    widget = HorizontalLinesWidget()
    widget.resize(400, 300)
    widget.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

"""

BOX_WIDTH = 13
BOX_HEIGHT = 13
HLINE_SPACING = 13 


class Tablature:
    def __init__(self, parent):
        self.parent = parent
        
        
    def draw_lines(self, qp):
        # Define some parameters
        line_color = QColor(0, 0, 0)  # Black color
        line_height = 13  # Divide the widget height by 7 to get 6 equal lines
        y = line_height

        # Draw 6 horizontal lines
        for _ in range(6):
            qp.setPen(line_color)
            qp.drawLine(0, y, self.parent.width(), y)
            y += line_height        
        
    def paintEvent(self, event):
        # called when parent.paintEvent event invoked.
        qp = QPainter(self.parent)
        qp.begin(self.parent)
        self.draw_lines(qp)
        qp.end()        
