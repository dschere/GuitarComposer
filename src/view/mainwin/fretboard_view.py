from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox

from view.widgets.filterableScaleSelector import FilterableScaleSelector
from view.widgets.fretboard import GuitarFretboard

from view.config import LabelText

class fretboard_view(QWidget):
    def __init__(self):
        super().__init__()

        fretboard = GuitarFretboard()
        scale_selector = FilterableScaleSelector()

        layout = QHBoxLayout()
        layout.addWidget(fretboard)

        group_box = QGroupBox(LabelText.scale_selector_group)
        group_box.setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 5px; margin-top: 10px; }"
                                "QGroupBox::title { subcontrol-origin: margin; padding: 0 3px; }")

        group_layout = QVBoxLayout()
        group_layout.addWidget(scale_selector)
        group_box.setLayout(group_layout)

        layout.addWidget(group_box)

        self.setLayout(layout)


        