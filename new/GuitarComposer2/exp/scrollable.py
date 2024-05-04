import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QVBoxLayout, QWidget, QLabel

class ScrollableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # Create a vertical layout for the scrollable widget
        layout = QVBoxLayout(self)

        # Add some example content (labels) to the layout
        for i in range(20):
            label = QLabel(f"Label {i}")
            layout.addWidget(label)

        # Set the layout of the scrollable widget
        self.setLayout(layout)

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Scrollable Widget Example")
        self.setGeometry(100, 100, 1180, 640)

        # Create a scrollable area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its widget
        scroll_area.setGeometry(50, 50, 500, 300)  # Set the size and position of the scroll area

        # Create a scrollable widget (content widget)
        scrollable_widget = ScrollableWidget()
        scroll_area.setWidget(scrollable_widget)  # Set the scrollable widget as the widget of the scroll area

        # Set the scroll area as the central widget of the main window
        self.setCentralWidget(scroll_area)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

