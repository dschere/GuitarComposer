from PyQt6.QtWidgets import QToolBar, QVBoxLayout, QTreeView, QWidget, QMenu, QPushButton, QStyle
from PyQt6.QtGui import QStandardItemModel, QAction, QStandardItem, QIcon

from models.song import Song
from models.track import Track

from view.dialogs.TrackPropertiesDialog import TrackPropertiesDialog
from view.events import Signals, EditorEvent, DeleteTrack
from controllers.appcontroller import SongController
from view.config import LabelText

from PyQt6.QtCore import QModelIndex, Qt

from controllers.appcontroller import TrackItem
from controllers.appcontroller import PropertiesItem
from controllers.appcontroller import SongItem
from view.events import Signals, TrackItem, PropertiesItem, SongItem
from view.config import LabelText

from .songDelegate import SongDelegate


class Navigator(QWidget):

    initial_tree_model_update = True
    current_song : Song | None = None
    current_track : Track | None = None

    def update_tree_model(self, model):
        self.tree_model = model
        self.tree_view.setModel(model)
        #if not self.initial_tree_model_update:
        #    return
        #self.initial_tree_model_update = False
        self.tree_view.expandAll()

        # setup editing the first track
        parent = model.invisibleRootItem()
        if parent and model.rowCount() > 0:
            item = parent.child(0)
            if item:
                song = item.data()
                if song and len(song.tracks) > 0:
                    track = song.tracks[0]

                    evt = EditorEvent()
                    evt.ev_type = EditorEvent.ADD_MODEL
                    evt.model = track 

                    self.current_song = song 
                    self.current_track = track

                    Signals.editor_event.emit(evt)

    def on_tree_clicked(self, index: QModelIndex):
        # Get the clicked item
        if index.model() is None:
            return
        clicked_item = index.model().itemFromIndex(index) # type: ignore

        item = index.model().itemFromIndex(index) # type: ignore
        
        if isinstance(item, PropertiesItem):
            (track_model, track_qmodel_item) = item.data()
            dialog = TrackPropertiesDialog(self, track_model)
            dialog.show()
        elif isinstance(item, TrackItem):
            evt = EditorEvent()
            item = index.model().itemFromIndex(index) # type: ignore
            evt.ev_type = EditorEvent.ADD_MODEL  # type: ignore
            evt.model = item.data()

            self.current_track = evt.model
            song_model = item.parent().data()
            if song_model != self.current_song:
                Signals.song_selected.emit(song_model)    
            self.current_song = song_model

            Signals.editor_event.emit(evt)

        elif isinstance(item, SongItem):
            song_model = item.data()
            self.current_song = song_model 
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

    def on_item_update(self, item : QStandardItem):
        index = item.index() 
        self.tree_view.expand(index)

    def on_delete_track(self):
        evt = DeleteTrack(self.current_song, self.current_track)
        Signals.delete_track.emit(evt)

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

        delegate = SongDelegate(self.tree_view)
        self.tree_view.setItemDelegateForColumn(0, delegate)  # put button in first column

        
        layout = QVBoxLayout()

        # control_bar = QToolBar()
        # style = self.style() 
        # assert(style)

        # # Add button with standard "add" icon (plus symbol)
        # add_btn = QPushButton("+")
        # add_btn.setToolTip(LabelText.add_track)
        # add_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        # add_btn.clicked.connect(lambda : Signals.add_track.emit())

        # # Delete button with standard "trash" icon
        # del_btn = QPushButton("-")
        # del_btn.setToolTip(LabelText.del_track)
        # del_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        # del_btn.clicked.connect(self.on_delete_track)

        # control_bar.addWidget(add_btn)
        # control_bar.addWidget(del_btn)

        # self.add_track_btn = add_btn 
        # self.delete_track_btn = del_btn

#        layout.addWidget(control_bar)
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        Signals.update_navigator.connect(self.update_tree_model)
        Signals.tree_item_added.connect(self.on_item_update)
