from PyQt6.QtWidgets import QVBoxLayout, QTreeView, QWidget, QMenu
from PyQt6.QtGui import QStandardItemModel, QAction

from view.widgets.projectNavigator.TrackTreeNode import TrackTreeDialog
from view.events import Signals
from controllers.appcontroller import SongController
from view.config import LabelText

from PyQt6.QtCore import QModelIndex, Qt


class Navigator(QWidget):

    def update_tree_model(self, model):
        self.tree_model = model
        self.tree_view.setModel(model)

    def on_tree_clicked(self, index: QModelIndex):
        # Get the clicked item
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.text() == 'properties':
            item = index.model().itemFromIndex(index)
            (track_model, track_qmodel_item) = item.data()
            dialog = TrackTreeDialog(self, track_model, track_qmodel_item)
            dialog.show()

    def add_track(self, song_controller: SongController):
        song_controller.userAddTrack()
        self.tree_view.update()

    def showContextMenu(self, point):
        "right click "
        index = self.tree_view.indexAt(point)
        if index.isValid():
            right_clicked_item = index.model().itemFromIndex(index)
            obj = right_clicked_item.data()
            if isinstance(obj, SongController):
                menu = QMenu()
                action1 = QAction(LabelText.add_track, self)
                action1.triggered.connect(lambda: self.add_track(obj))
                menu.addAction(action1)
                menu.exec(self.tree_view.mapToGlobal(point))

    def __init__(self):
        super().__init__()

        # placeholder model for representing a TreeView
        self.tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setEditTriggers(
            QTreeView.EditTrigger.DoubleClicked |
            QTreeView.EditTrigger.SelectedClicked)
        self.tree_view.clicked.connect(self.on_tree_clicked)
        self.tree_view.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.showContextMenu)

        layout = QVBoxLayout()
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        Signals.update_navigator.connect(self.update_tree_model)
