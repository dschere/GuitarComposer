import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

class RotatedRectangleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotated Rectangle")
        self.setGeometry(0, 0, 100, 100)  # Adjust window size as needed
        #self.setBackgroundRole(self.Palette.Dark)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Optional: enable antialiasing for smoother lines

        
        
        # Set the rectangle parameters
        rect_width = 50
        rect_height = 50
        rect_angle = 45  # Rotation angle in degrees
        rect_color = QColor("gold")
        rect_pen = QPen(rect_color, 3, Qt.PenStyle.SolidLine)
        rect_brush_color = QColor("green")  # Fill color
        
        painter.drawLine(0,50,100,50)

        # Translate and rotate the painter to draw the rotated rectangle
        painter.translate(self.width() // 2, self.height() // 2)  # Center the drawing
        painter.rotate(rect_angle)
        
        # Set the pen and brush for drawing
        painter.setPen(rect_pen)
        painter.setBrush(rect_brush_color)  # Set the fill color
        
        # Draw the rotated rectangle
        painter.drawRect(-rect_width // 2, -rect_height // 2, rect_width, rect_height)
        
        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = RotatedRectangleWidget()
    widget.show()
    sys.exit(app.exec())

