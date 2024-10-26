from PyQt6.QtWidgets import QVBoxLayout, QTreeView, QWidget
from PyQt6.QtGui import QStandardItemModel

from view.widgets.projectNavigator.TrackTreeNode import TrackTreeDialog
from view.events import Signals
from PyQt6.QtCore import QModelIndex

class Navigator(QWidget):

    def update_tree_model(self, model):
        self.tree_model = model
        self.tree_view.setModel(model)

    
    def on_tree_clicked(self, index: QModelIndex):
        # Get the clicked item
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.text() == 'properties':
            item = index.model().itemFromIndex(index)
            track_model = item.data()
            dialog = TrackTreeDialog(self, track_model)  
            dialog.show() 
        
    def __init__(self):
        super().__init__()

        # placeholder model for representing a TreeView
        self.tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.SelectedClicked)
        self.tree_view.clicked.connect(self.on_tree_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        Signals.update_navigator.connect(self.update_tree_model)