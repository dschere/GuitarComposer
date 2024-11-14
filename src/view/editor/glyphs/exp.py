from PyQt6.QtGui import QPainter, QPalette
from PyQt6.QtWidgets import QApplication, QWidget
import qdarktheme

app = QApplication([])
app.setStyleSheet(qdarktheme.load_stylesheet())


class ThemedWidget(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        palette = self.palette()  # Get the widget's palette for theme colors
        background_color = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)

        # Fill background
        painter.fillRect(event.rect(), background_color)

        # Set text color and draw text
        painter.setPen(text_color)
        painter.drawText(10, 30, "Hello, themed world!")

        painter.end()


# Usage example
window = ThemedWidget()
window.show()
app.exec()
