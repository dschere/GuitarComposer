"""
High level controller for the main window

"""
import json
import uuid
import logging

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtCore import QTimer, QSettings
from PyQt6.QtCore import Qt

from models.note import Note
from models.song import Song
from models.track import Track
from view.events import Signals
from util.projectRepo import ProjectRepo
from music.instrument import Instrument
from view.config import LabelText

FRETBOARD_CHANNEL = 0


class SongController:
    def __init__(self, title):
        self.song = Song()
        self.song.title = title
        self.instruments = {}

    def load_model(self, s: Song):
        self.song = s
        for track in self.song.tracks:
            instrument = Instrument(track.instrument_name)
            self.instruments[track.instrument_name] = instrument

    def title(self):
        return self.song.title

    def createQModel(self):
        "generate a tree structure for this song"
        root = QStandardItem(">> " + self.song.title)
        for (i, track) in enumerate(self.song.tracks):
            n = i + 1
            track_item = QStandardItem(LabelText.track + f" {n}")
            properties_item = QStandardItem(LabelText.properties)

            # Set the icon and text for the 'Properties' node
            gear_icon = QIcon.fromTheme("emblem-system")
            properties_item.setIcon(gear_icon)

            # associate our track model with the tree model used for visualization
            properties_item.setData(track)

            track_item.appendRow(properties_item)
            root.appendRow(track_item)
        return root

    def addTrack(self, instr_name):
        # assign synth channel(s) to play the instrument
        instrument = Instrument(instr_name)

        # build data structure
        track = Track()
        track.uuid = str(uuid.uuid4())
        track.instrument_name = instr_name
        self.song.tracks.append(track)

        # map the instrument name to a syn interface
        self.instruments[instr_name] = instrument

    def removeTrack(self, instr_name):
        # TODO, must add checkin/checkout capability to the
        # channel manager in the synth service.
        pass


def log_model_contents(model: QStandardItemModel):
    # Get the number of rows and columns in the model
    row_count = model.rowCount()
    column_count = model.columnCount()

    logging.debug("Navigator tree model contents")
    logging.debug(f"  row_count = {row_count}, column_count = {column_count}")
    # Loop through each row and column
    for row in range(row_count):
        for column in range(column_count):
            # Get the item at the given row and column
            item = model.item(row, column)
            if item:
                # Log the item's data (display role by default)
                logging.debug(
                    f"    Row {row}, Column {column}: {item.data(Qt.ItemDataRole.DisplayRole)}")


class AppController:
    settings_key = __name__+".active_song_titles"

    def update_navigator(self):
        "construct a QModel for the treeView"
        root = QStandardItemModel()
        root.setHorizontalHeaderLabels(["Guitar Composer"])
        for title in sorted(self.song_ctrl):
            sc = self.song_ctrl[title]
            song_item = sc.createQModel()
            root.appendRow(song_item)

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            titles = sorted(self.song_ctrl)
            logging.debug("setup controllers for %s" % str(titles))
            log_model_contents(root)

        # send to navigator widget
        Signals.update_navigator.emit(root)

    def on_ready(self, app):
        # setup navigator, score editor
        titles = self.projects.getTitles()

        if len(titles) == 0:
            sc = SongController("noname")
            sc.addTrack('Acoustic Guitar')
            self.song_ctrl[sc.title()] = sc
        else:
            for title in titles:
                song_model = self.projects.load_song(title)
                sc = SongController(title)
                sc.load_model(song_model)
                self.song_ctrl[sc.title()] = sc

        self.update_navigator()

    def on_load_settings(self, settings: QSettings):
        if settings.contains(self.settings_key):
            val = settings.value(self.settings_key)
            self.active_song_titles = set(json.loads(val))

    def on_save_settings(self, settings: QSettings):
        val = json.dumps(list(self.active_song_titles))
        settings.setValue(self.settings_key, val)

    def __init__(self, synth_service):
        self.synth_service = synth_service

        self.projects = ProjectRepo()
        self.active_song_titles = set()
        self.song_ctrl = {}

        # current track being edited.
        self.current_track = None

        Signals.preview_play.connect(self.handle_preview_play)
        Signals.preview_stop.connect(self.handle_preview_stop)

        Signals.load_settings.connect(self.on_load_settings)
        Signals.save_settings.connect(self.on_load_settings)

        Signals.ready.connect(self.on_ready)

    def handle_preview_play(self, n: Note):
        self.synth_service.noteon(FRETBOARD_CHANNEL, n.midi_code, n.velocity)

    def handle_preview_stop(self, n: Note):
        self.synth_service.noteoff(FRETBOARD_CHANNEL, n.midi_code)
