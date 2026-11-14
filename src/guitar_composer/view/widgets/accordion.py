import sys
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy
)


HINT_PAD = 50

class AccordionSection(QWidget):


    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)

        self.content_being_shown = False
        self.last_content_height = 0
        self.toggle_button = QPushButton(f"▶  {title}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("""
            QPushButton:checked {
                background-color: grey;
                color: blue;
                text-align: left; padding-left: 10px;    
            }
            QPushButton {
                text-align: left; padding-left: 10px;
            }
        """)

        
        self.content_area = QFrame()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
   
   
        content_layout = QVBoxLayout(self.content_area)
        content_layout.addWidget(content_widget)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        self.toggle_button.toggled.connect(self.toggle)



    def toggle(self, checked: bool):
        title_text = self.toggle_button.text()[3:]
        self.toggle_button.setText(f"{'▼' if checked else '▶'}  {title_text}")

        content_height = self.content_area.layout().sizeHint().height() + HINT_PAD
        self.animation.setStartValue(0 if checked else content_height)
        self.animation.setEndValue(content_height if checked else 0)
        self.animation.start()

        self.content_being_shown = checked
        self.last_content_height = content_height

class Accordion(QWidget):

    def __init__(self, exclusive: bool = True, parent=None):
        super().__init__(parent)
        self.exclusive = exclusive
        self.sections = []
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.addStretch()

    def content_updated(self):
        for section in self.sections:
            if section.content_being_shown:
                content_height = section.content_area.layout().sizeHint().height() + HINT_PAD
                if content_height == section.last_content_height:
                    continue

                section.animation.setStartValue(section.last_content_height)
                section.animation.setEndValue(content_height)
                section.animation.start()
                section.last_content_height = content_height

    def add_section(self, title: str, widget: QWidget):
        section = AccordionSection(title, widget)
        section.toggle_button.toggled.connect(
            lambda checked, s=section: self._on_section_toggled(s, checked)
        )
        self.sections.append(section)
        self.layout.insertWidget(self.layout.count() - 1, section)

    def _on_section_toggled(self, active_section: AccordionSection, checked: bool):
        if self.exclusive and checked:
            for section in self.sections:
                if section is not active_section and section.toggle_button.isChecked():
                    section.toggle_button.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.resize(400, 300)

    accordion = Accordion(exclusive=False)
    accordion.add_section("Accordion Item #1", QLabel("Content for the first section."))
    accordion.add_section("Accordion Item #2", QLabel("Content for the second section."))
    accordion.add_section("Accordion Item #3", QLabel("Content for the third section."))

    layout = QVBoxLayout(window)
    layout.addWidget(accordion)
    window.show()
    sys.exit(app.exec())
