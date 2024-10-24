from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QVBoxLayout, QPushButton, QToolBar, QApplication, QTreeView, QComboBox, QStyledItemDelegate, QWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor
from PyQt6.QtCore import Qt

from music.instrument import getInstrumentList
from view.config import LabelText


class InstrumentSelector(QWidget):
    instrument_names = getInstrumentList()

    def _on_instruments_selection(self):
        pass

    def _filter_instruments(self):
        filter_text = self.filter_input.text().lower()
        self.instruments_combo_box.clear()

        # Filter combo box items based on the text input
        filtered_items = [
            item for item in self.items if filter_text in item.lower()]
        self.instruments_combo_box.addItems(filtered_items)


    def __init__(self, parent):
        super().__init__()
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
        self.instruments_combo_box.currentIndexChanged.connect(
            self._on_instruments_selection)

        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.instruments_combo_box)

        # add to main layout
        main_layout.addLayout(filter_layout)
        main_layout.addLayout(combo_layout)

        self.setLayout(main_layout)



class ProjectDelegate(QStyledItemDelegate):
    """Custom delegate for rendering a dropdown (QComboBox) in the 'Instrument' node."""
    def createEditor(self, parent, option, index):
        if index.data() == "Instrument":  # Apply only to the 'Instrument' node
            editor = QComboBox(parent)
            editor.addItems(getInstrumentList())
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

