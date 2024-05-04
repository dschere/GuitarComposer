import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QFontMetrics

class RoundedBorderWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.setMinimumSize(200, 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Enable anti-aliasing for smooth edges

        # Define the background color and border color
        background_color = QColor(240, 240, 240)
        border_color = QColor(100, 100, 100)

        # Set painter colors
        painter.setBrush(background_color)
        painter.setPen(border_color)

        # Calculate the rectangle for the rounded border
        rect = self.rect().adjusted(5, 5, -5, -5)  # Adjust for padding
        print(rect)

        # Draw the rounded rectangle border
        painter.drawRoundedRect(rect, 10, 10)

        # Draw the title text centered inside the border
        font = self.font()
        font.setBold(True)
        painter.setFont(font)

        text_rect = painter.boundingRect(rect, 0, self.title)
        text_x = int(rect.x() + (rect.width() - text_rect.width()) / 2)
        text_y = int(rect.y() + 20)  # Adjust vertical position
        painter.drawText(text_x, text_y, self.title)

def main():
    app = QApplication(sys.argv)

    # Create and show the custom widget with rounded border and title
    widget = RoundedBorderWidget("Widget Title")
    widget.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()

