from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFrame, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, QPropertyAnimation

class CollapsiblePanel(QWidget):
    def __init__(self, title, content_widget, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        # Header button
        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.toggle_panel)
        self.layout().addWidget(self.toggle_button) # type: ignore

        # Content area
        self.content_area = QFrame()
        self.content_area.setLayout(QVBoxLayout())
        self.content_area.layout().addWidget(content_widget) # type: ignore
        self.content_area.setMaximumHeight(0)  # Start collapsed
        self.content_area.setVisible(False)
        self.layout().addWidget(self.content_area) # type: ignore

        # Animation for smooth transition
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)

    def toggle_panel(self):
        if self.toggle_button.isChecked():
            self.content_area.setVisible(True)
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.content_area.sizeHint().height())
        else:
            self.animation.setStartValue(self.content_area.height())
            self.animation.setEndValue(0)
            self.animation.finished.connect(lambda: self.content_area.setVisible(False))
        self.animation.start()

class AccordionDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accordion Layout")
        self.setGeometry(100, 100, 400, 300)

        # Scroll area to handle many items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        accordion_content = QWidget()
        accordion_layout = QVBoxLayout()
        accordion_content.setLayout(accordion_layout)
        scroll_area.setWidget(accordion_content)
        main_layout.addWidget(scroll_area)

        # Add collapsible panels to accordion
        for i in range(5):
            panel = CollapsiblePanel(f"Section {i + 1}", QLabel(f"Content for Section {i + 1}"))
            accordion_layout.addWidget(panel)

        accordion_layout.addStretch()  # Add space at the bottom

if __name__ == "__main__":
    app = QApplication([])
    window = AccordionDemo()
    window.show()
    app.exec()
