import sys
from PyQt6.QtWidgets import (QApplication,
                             QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLineEdit, QLabel, QPushButton)


from util.scale import MusicScales
from view.config import LabelText
from view.events import Signals, ScaleSelectedEvent, ClearScaleEvent
from music.instrument import getInstrumentList


class FilterableScaleSelector(QWidget):

    def on_inst_select(self):
        name = self.instr_combo_box.currentText()
        Signals.fretboard_inst_select.emit(name)

    def __init__(self):
        super().__init__()

        self.scale_widget_name = __class__.__name__ + ".scale"
        self.key_widget_name = __class__.__name__ + ".key"
        self.filter_widget_name = __class__.__name__ + ".filter"

        self.music_scales = MusicScales()

        # Main vertical layout
        main_layout = QVBoxLayout()

        instrument_layout = QHBoxLayout()
        instrument_label = QLabel(LabelText.instruments)
        self.instr_combo_box = QComboBox()
        instr_list = getInstrumentList()
        self.instr_combo_box.addItems(instr_list)
        instrument_layout.addWidget(instrument_label)
        instrument_layout.addWidget(self.instr_combo_box)

        # Create the filter label and filter input
        filter_layout = QHBoxLayout()
        filter_label = QLabel(LabelText.filter_scale, self)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter...")
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)

        # Create the combo box label and combo box
        combo_layout = QHBoxLayout()
        combo_label = QLabel(LabelText.scales, self)
        self.scale_combo_box = QComboBox(self)
        s_names = self.music_scales.sorted_names
        self.items = list(filter(lambda n: len(n) < 48, s_names))
        self.scale_combo_box.addItems(self.items)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.scale_combo_box)

        key_layout = QHBoxLayout()
        key_label = QLabel(LabelText.keys, self)
        self.key_combo_box = QComboBox()
        key_items = ["A", "A#/Bb", "B", "C", "C#/Db",
                     "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab"]
        self.key_combo_box.addItems(key_items)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_combo_box)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton(LabelText.clear_scale)
        clear_btn.clicked.connect(self.on_clear_click)
        btn_layout.addWidget(clear_btn)

        # Add horizontal layouts to the main vertical layout
        main_layout.addLayout(instrument_layout)
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(combo_layout)
        main_layout.addLayout(key_layout)
        main_layout.addLayout(btn_layout)

        # No margins around the layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        # Set layout to the window
        self.setLayout(main_layout)

        # Connect filter input to filtering method
        self.filter_input.textChanged.connect(self.filter_items)

        self.scale_combo_box.currentIndexChanged.connect(
            self.on_scale_selection)
        self.key_combo_box.currentIndexChanged.connect(self.on_scale_selection)
        self.instr_combo_box.currentIndexChanged.connect(self.on_inst_select)

        Signals.load_settings.connect(self.on_load_settings)
        Signals.save_settings.connect(self.on_save_settings)

    def on_load_settings(self, settings):
        if settings.contains(self.scale_widget_name):
            self.scale_combo_box.setCurrentText(
                settings.value(self.scale_widget_name))
        if settings.contains(self.key_widget_name):
            self.key_combo_box.setCurrentText(
                settings.value(self.key_widget_name))

    def on_save_settings(self, settings):
        settings.setValue(self.scale_widget_name,
                          self.scale_combo_box.currentText())
        settings.setValue(self.key_widget_name,
                          self.key_combo_box.currentText())

    def on_clear_click(self, *args):
        Signals.clear_scale.emit(ClearScaleEvent())

    def on_scale_selection(self, *args):
        # capture selection and compute midi codes
        scale_name = self.scale_combo_box.currentText()
        key = self.key_combo_box.currentText().split("/")[0]
        if len(scale_name) == 0:
            return

        (mc_list, seq) = \
            self.music_scales.generate_midi_scale_codes(
                scale_name, key)

        # emit message
        msg = ScaleSelectedEvent()
        msg.key = key
        msg.scale_midi = mc_list
        msg.scale_seq = seq
        Signals.scale_selected.emit(msg)

    def filter_items(self):
        filter_text = self.filter_input.text().lower()
        self.scale_combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [
            item for item in self.items if filter_text in item.lower()]
        self.scale_combo_box.addItems(filtered_items)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FilterableScaleSelector()

    def msg_handler(obj):
        print(vars(obj))
    Signals.scale_selected.connect(msg_handler)

    window.show()
    sys.exit(app.exec())
