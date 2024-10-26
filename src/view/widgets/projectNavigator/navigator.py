from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QVBoxLayout, QPushButton, QToolBar, QApplication, QTreeView, QComboBox, QStyledItemDelegate, QWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor
from PyQt6.QtCore import Qt

from view.widgets.projectNavigator.TrackTreeNode import TrackTreeNode
from view.events import Signals
import logging

class ProjectDelegate(QStyledItemDelegate):
    """Custom delegate for rendering a dropdown (QComboBox) in the 'Instrument' node."""
    def createEditor(self, parent, option, index):
        if index.data() == "Instrument":  # Apply only to the 'Instrument' node
            item = index.model().itemFromIndex(index)
            track_model = item.data()
            track_widget = TrackTreeNode(track_model)
            track_widget.setParent(parent)
            return track_widget
        return super().createEditor(parent, option, index)

class Navigator(QWidget):

    def update_tree_model(self, model):
        logging.debug("setting up navigator model")
        print(model)
        self.tree_view.setModel(model)
        self.tree_view.update()

    def __init__(self):
        super().__init__()
        # qt's model for representing a TreeView
        tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(tree_model)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.SelectedClicked)

        # Add delegate to handle dropdown for the 'Instrument' node only
        delegate = ProjectDelegate()
        self.tree_view.setItemDelegate(delegate)  # Apply the delegate globally, but it will only affect the 'Instrument' node

        layout = QVBoxLayout()
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        Signals.update_navigator.connect(self.update_tree_model)