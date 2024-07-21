import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath
from PyQt6.QtCore import Qt

class CustomIcon(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Icon Example")
        self.setFixedSize(100, 100)  # Set the size of the widget

        # Create a white plus sign on a green background
        icon_size = 100  # Icon size (square)
        icon = self.createIcon(icon_size)
        
        # Set the window icon
        self.setWindowIcon(QIcon(icon))

    def createIcon(self, size):
        # Create a QPixmap to draw the icon
        pixmap = QPixmap(size, size)
        #pixmap.fill(Qt.transparent)  # Make the pixmap transparent
        
        # Create a QPainter to draw on the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw green circle background
        painter.setBrush(QColor("#4CAF50"))  # Green color
        #painter.setPen(Qt.NoPen)  # No outline
        painter.drawEllipse(0, 0, size, size)
        
        # Draw white plus sign
        pen_color = Qt.white
        pen_width = 4
        painter.setPen(pen_color)
        painter.setBrush(Qt.NoBrush)  # No fill
        center = size / 2
        half_width = 0.5 * pen_width
        path = QPainterPath()
        path.moveTo(center - half_width, half_width)
        path.lineTo(center + half_width, half_width)
        path.lineTo(center + half_width, center - half_width)
        path.lineTo(center + half_width, center + half_width)
        path.lineTo(center - half_width, center + half_width)
        path.lineTo(center - half_width, center - half_width)
        painter.drawPath(path)

        painter.end()  # Finish painting

        return pixmap

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CustomIcon()
    window.show()
    sys.exit(app.exec())

