import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QLabel


from util.scale import MusicScales
from view.config import LabelText
from view.events import Signals, ScaleSelectedEvent
        

class FilterableScaleSelector(QWidget):
    

    def __init__(self):
        super().__init__()
        self.music_scales = MusicScales()

        # Main vertical layout
        main_layout = QVBoxLayout()

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
        self.combo_box = QComboBox(self)
        s_names = self.music_scales.sorted_names
        self.items = list(filter(lambda n: len(n) < 48, s_names))
        self.combo_box.addItems(self.items)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.combo_box)

        key_layout = QHBoxLayout()
        key_label = QLabel(LabelText.keys, self)
        self.key_combo_box = QComboBox()
        key_items = ["A","A#/Bb","B","C","C#/Db","D","D#/Eb","E","F","F#/Gb","G","G#/Ab"]
        self.key_combo_box.addItems(key_items)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_combo_box) 

        # Add horizontal layouts to the main vertical layout
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(combo_layout)
        main_layout.addLayout(key_layout)

        # Set layout to the window
        self.setLayout(main_layout)

        # Connect filter input to filtering method
        self.filter_input.textChanged.connect(self.filter_items)

        self.combo_box.currentIndexChanged.connect(self.on_scale_selection)

    def on_scale_selection(self, *args):
        # capture selection and compute midi codes
        scale_name = self.combo_box.currentText()
        key = self.key_combo_box.currentText().split("/")[0]
        (mc_list,seq) = self.music_scales.generate_midi_scale_codes(scale_name, key)
        
        # emit message
        msg = ScaleSelectedEvent()
        msg.key = key
        msg.scale_midi = mc_list
        msg.scale_seq = seq
        Signals.scale_selected.emit(msg)

    def filter_items(self):
        filter_text = self.filter_input.text().lower()
        self.combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [item for item in self.items if filter_text in item.lower()]
        self.combo_box.addItems(filtered_items)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FilterableScaleSelector()
    
    def msg_handler(obj):
        print(vars(obj))
    Signals.scale_selected.connect(msg_handler)

    window.show()
    sys.exit(app.exec())
