from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QVBoxLayout, QComboBox, QWidget
from PyQt6.QtCore import Qt

from music.instrument import getInstrumentList
from view.config import LabelText
from view.events import Signals, InstrumentSelectedEvent 

""" 
The sub widget that draws a 

  <filter instrument list>
  <instrument list combo box>

* able to route an instrument selected to asignal and pass
  along the track associated with this event
* able to filter the instrument list    
"""
class TrackTreeNode(QWidget):
    instrument_names = getInstrumentList()
    title = "Instrument"


    def _filter_instruments(self):
        filter_text = self.filter_input.text().lower()
        self.instruments_combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [
            item for item in self.items if filter_text in item.lower()]
        self.instruments_combo_box.addItems(filtered_items)

    def _on_instrument_selected(self):
        evt = InstrumentSelectedEvent()
        evt.instrument = self.instruments_combo_box.currentText()
        evt.track = self.track_model
        Signals.instrument_selected.emit(evt)

    def __init__(self, track_model):
        super().__init__()

        self.track_model = track_model

        # filtered drop down menu to select an instrument
        main_layout = QVBoxLayout()

        # line 1 is text box that allows the user to search an instrument.
        filter_layout = QHBoxLayout()
        filter_label = QLabel(LabelText.filter_instruments, self)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self._filter_instruments)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)

        # line 2 is a combobox of sorted instruments
        combo_layout = QHBoxLayout()
        combo_label = QLabel(LabelText.instruments, self)
        self.instruments_combo_box = QComboBox(self)
        self.instruments_combo_box.addItems(self.instrument_names)
        f = self._on_instrument_selected
        self.instruments_combo_box.currentIndexChanged.connect(f)

        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.instruments_combo_box)

        # add to main layout
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(combo_layout)

        self.setLayout(main_layout)

        
