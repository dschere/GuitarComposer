import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QLabel, QVBoxLayout, QWidget, QScrollArea
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QRect

class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 600)  # Set minimum size for the canvas

    def paintEvent(self, event):
        # Example drawing on the canvas using QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Optional: enable antialiasing
        painter.fillRect(self.rect(), QColor(Qt.GlobalColor.white))  # Fill background with white

        # Draw text in the center of the canvas
        text_rect = QRect(self.rect())
        painter.setPen(QColor(Qt.GlobalColor.red))
        painter.setFont(QFont('Arial', 20))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, 'Scrollable Canvas Widget')

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Splitter Example")
        self.setGeometry(100, 100, 800, 600)

        # Create a splitter widget
        splitter = QSplitter(self)
        splitter.setGeometry(0, 0, 800, 600)  # Adjust geometry as needed

        # Left widget (fixed size)
        left_widget = QLabel("Fixed Left Widget", splitter)
        left_widget.setFixedSize(200, 600)  # Fixed width, full height

        # Right widget (scrollable canvas)
        scrollable_widget = QWidget(splitter)
        scrollable_widget.setMinimumSize(400, 600)  # Set minimum size for scrollable widget
        scrollable_layout = QVBoxLayout(scrollable_widget)
        canvas_widget = CanvasWidget()
        scrollable_layout.addWidget(canvas_widget)

        # Create a scroll area and set the scrollable widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scrollable_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Enable horizontal scroll bar

        # Add widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(scroll_area)

        # Set the size policy for the splitter
        splitter.setStretchFactor(0, 0)  # Left widget does not stretch
        splitter.setStretchFactor(1, 1)  # Right widget (scroll area) stretches

        # Set the main widget of the QMainWindow
        self.setCentralWidget(splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
