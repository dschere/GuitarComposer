from PyQt6.QtWidgets import QApplication, QTreeView, QComboBox, QStyledItemDelegate
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt


class InstrumentDelegate(QStyledItemDelegate):
    """Custom delegate for rendering a dropdown (QComboBox) in the 'Instrument' node."""
    def createEditor(self, parent, option, index):
        if index.data() == "Instrument":  # Apply only to the 'Instrument' node
            editor = QComboBox(parent)
            editor.addItems(["Piano", "Guitar", "Drums", "Bass", "Violin"])
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


def create_track_node(track_name):
    track = QStandardItem(track_name)

    # Add measures horizontally
    measures_item = QStandardItem("Measures")
    for i in range(1, 5):
        measure = QStandardItem(f"Measure {i}")
        measures_item.appendRow(measure)
    track.appendRow(measures_item)

    # Add properties node with instrument dropdown
    properties_item = QStandardItem("Properties")
    instrument_item = QStandardItem("Instrument")
    instrument_item.setEditable(True)  # This will allow the dropdown to be editable only for this node
    properties_item.appendRow(instrument_item)
    track.appendRow(properties_item)

    return track


def create_song_node(song_name):
    song = QStandardItem(song_name)

    # Create tracks node
    tracks_item = QStandardItem("Tracks")

    # Add track nodes
    for track_index in range(1, 4):
        track_item = create_track_node(f"Track {track_index}")
        tracks_item.appendRow(track_item)

    song.appendRow(tracks_item)
    return song


def create_project_structure():
    # Create the root item (Project)
    root_item = QStandardItem("Project")

    # Create song nodes
    for song_index in range(1, 3):
        song_item = create_song_node(f"Song {song_index}")
        root_item.appendRow(song_item)

    return root_item


if __name__ == '__main__':
    app = QApplication([])

    # Create the model and the root node (project)
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Project Structure"])
    root_item = create_project_structure()
    model.appendRow(root_item)

    # Create the tree view and set the model
    tree_view = QTreeView()
    tree_view.setModel(model)
    tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.SelectedClicked)

    # Add delegate to handle dropdown for the 'Instrument' node only
    delegate = InstrumentDelegate()
    tree_view.setItemDelegate(delegate)  # Apply the delegate globally, but it will only affect the 'Instrument' node

    tree_view.setWindowTitle("Project Tree")
    tree_view.resize(600, 400)
    tree_view.show()

    app.exec()
