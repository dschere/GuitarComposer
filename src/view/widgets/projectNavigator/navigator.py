from PyQt6.QtWidgets import QVBoxLayout, QTreeView, QWidget, QMenu
from PyQt6.QtGui import QStandardItemModel, QAction

from view.widgets.projectNavigator.TrackTreeNode import TrackTreeDialog
from view.events import Signals, EditorEvent
from controllers.appcontroller import SongController
from view.config import LabelText

from PyQt6.QtCore import QModelIndex, Qt

from controllers.appcontroller import TrackItem
from controllers.appcontroller import PropertiesItem
from controllers.appcontroller import SongItem


class Navigator(QWidget):

    def update_tree_model(self, model):
        self.tree_model = model
        self.tree_view.setModel(model)

    def on_tree_clicked(self, index: QModelIndex):
        # Get the clicked item
        assert(index.model())
        clicked_item = index.model().itemFromIndex(index) # type: ignore

        item = index.model().itemFromIndex(index) # type: ignore
        
        if isinstance(item, PropertiesItem):
            (track_model, track_qmodel_item) = item.data()
            dialog = TrackTreeDialog(self, track_model, track_qmodel_item)
            dialog.show()
        elif isinstance(item, TrackItem):
            evt = EditorEvent()
            item = index.model().itemFromIndex(index) # type: ignore
            evt.ev_type = EditorEvent.ADD_MODEL  # type: ignore
            evt.model = item.data()
            Signals.editor_event.emit(evt)
        elif isinstance(item, SongItem):
            song_model = item.data() 
            Signals.song_selected.emit(song_model)    


    def add_track(self, song_controller: SongController):
        song_controller.userAddTrack()
        self.tree_view.update()

    def showContextMenu(self, point):
        "right click "
        index = self.tree_view.indexAt(point)
        if index.isValid() and index.model():
            right_clicked_item = index.model().itemFromIndex(index) # type: ignore
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
