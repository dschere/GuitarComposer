from PyQt6.QtWidgets import QApplication, QTreeView, QComboBox, QStyledItemDelegate
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from music.instrument import getInstrumentList

""" 
Projects<root>
   Song
      Tracks
         track
         track
            instrument
      Properties
         title
         author
"""


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
