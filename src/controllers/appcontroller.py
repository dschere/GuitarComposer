"""
High level controller for the main window

"""
import json
import copy
import logging

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtCore import QSettings, pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from models.effect import Effect
from models.note import Note
from models.song import Song
from models.track import Track
from view.events import Signals, StringBendEvent
from services.projectMngr import ProjectManager
from music.instrument import Instrument
from view.config import LabelText

from view.dialogs.effectsControlDialog.dialog import EffectPreview,\
    EffectChanges

from view.events import Signals, TrackItem, PropertiesItem, SongItem


FRETBOARD_CHANNEL = 0


class SongController:

    def on_track_change(self, track: Track):
        """
        Ensure that the same number of measures and beats exists
        for all tracks after a track has has a new element added
        or removed from it.

        If poly ythm tracks is enabled there is no synthchronization.
        different tracks may have independent time signatures. 
        
        """
        if not self.song.poly_rythm_tracks:
            pass

    def open_song(self):
        saved_song = ProjectManager().open_song_using_title(self.song.title)
        if not saved_song:
            saved_song = ProjectManager().open_song_using_dialog()
            
        if saved_song:
            self.song = saved_song


    def __init__(self, title):
        self.song = Song()
        self.song.title = title
        self.instruments = {}
        self.q_model = None

        Signals.track_update.connect(self.on_track_change)
        Signals.open_song.connect(self.open_song)

    def __del__(self):
        try:
            Signals.open_song.disconnect(self.open_song)
            Signals.track_update.disconnect(self.on_track_change)
        except RuntimeError:
            # Possible that Signals has been deleted. 
            pass

    def setTitle(self, title):
        self.song.title = title

    def getTitle(self):
        return self.song.title

    def load_model(self, s: Song):
        self.song = s
        for track in self.song.tracks:
            instrument = Instrument(track.instrument_name)
            self.instruments[track] = instrument


    def title(self):
        return self.song.title

    def addQTrackModel(self, track, root):
        n = track.instrument_name
        track_item = TrackItem(LabelText.track + f": {n}")
        properties_item = PropertiesItem(LabelText.properties)

        track_item.setData(track)

        flags = properties_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        properties_item.setFlags(flags)

        flags = track_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        track_item.setFlags(flags)

        # Set the icon and text for the 'Properties' node
        gear_icon = QIcon.fromTheme("emblem-system")
        properties_item.setIcon(gear_icon)

        # associate our track model with the tree model
        # used for visualization
        properties_item.setData((track, track_item,))

        track_item.appendRow(properties_item)
        root.appendRow(track_item)

        # publish event 
        Signals.tree_item_added.emit(track_item)
        Signals.tree_item_added.emit(properties_item)
          
    def createQModel(self):
        "generate a tree structure for this song"
        root = SongItem(self.song.title)
        root.setData(self.song)

        for track in self.song.tracks:
            self.addQTrackModel(track, root)

        self.q_model = root
        return root

    def userAddTrack(self):
        if not self.q_model:
            logging.error("userAddTrack called but we have not setup model!")
            return

        track = self.addTrack('12-str.GT')
        self.addQTrackModel(track, self.q_model)

    def addTrack(self, instr_name):
        # assign synth channel(s) to play the instrument
        instrument = Instrument(instr_name)

        # build data structure
        track = Track()
        #track.uuid = str(uuid.uuid4())
        track.instrument_name = instr_name
        self.song.tracks.append(track)

        # map the instrument name to a syn interface
        self.instruments[track] = instrument

        return track

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
                v = item.data(Qt.ItemDataRole.DisplayRole)
                # Log the item's data (display role by default)
                logging.debug(
                    f"    Row {row}, Column {column}: {v}")


class AppController:
    settings_key = __name__+".active_song_titles"

    def on_song_title_changed(self, item):
        new_text = item.text()
        s_ctl = item.data()

        is_song_ctl = False
        try:
            if isinstance(s_ctl, SongController):
                is_song_ctl = True
        except TypeError:
            pass

        if is_song_ctl:
            if new_text == s_ctl.getTitle():
                pass  # no-op we didn't change anything
            # user has edited the song title, check for collissions
            elif new_text in self.song_ctrl:
                QMessageBox.critical(None,
                                     "Error", f"{new_text} already exists!",
                                     QMessageBox.StandardButton.Ok)
            else:
                s_ctl.setTitle(new_text)

    def update_navigator(self):
        "construct a QModel for the treeView"
        root = QStandardItemModel()
        root.itemChanged.connect(self.on_song_title_changed)
        root.setHorizontalHeaderLabels(["Guitar Composer"])
        default_song_selected = None

        for title in sorted(self.song_ctrl):
            sc = self.song_ctrl[title]
            if not default_song_selected:
                default_song_selected = sc.song 
                
            song_item = sc.createQModel()
            root.appendRow(song_item)

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            titles = sorted(self.song_ctrl)
            logging.debug("setup controllers for %s" % str(titles))
            log_model_contents(root)

        # send to navigator widget
        Signals.update_navigator.emit(root)
        Signals.song_selected.emit(default_song_selected)

    def on_ready(self, app):
        # setup navigator, score editor
        titles = self.projects.titles()

        if len(titles) == 0:
            sc = SongController("noname")
            sc.addTrack('12-str.GT')
            self.song_ctrl[sc.title()] = sc
        else:
            for title in titles:
                song_model = self.projects.open_song_using_title(title)
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

    def on_preview_instr_changed(self, instrument_name):
        self.preview_instr.free_resources()
        self.preview_instr = Instrument(instrument_name)

    def __init__(self, synth_service):
        self.synth_service = synth_service
        self.editor_ctrl = None

        self.projects = ProjectManager()
        self.active_song_titles = set()
        self.song_ctrl = {}
        self.preview_instr = Instrument("12-str.GT")
        Signals.fretboard_inst_select.connect(self.on_preview_instr_changed)

        # current track being edited.
        self.current_track = None

        Signals.preview_play.connect(self.handle_preview_play)
        Signals.preview_stop.connect(self.handle_preview_stop)
        Signals.preview_effect.connect(self.handle_effects_preview)
        Signals.preview_pitch_change.connect(self.handle_pitch_change_preview_event)

        Signals.load_settings.connect(self.on_load_settings)
        Signals.save_settings.connect(self.on_load_settings)

        Signals.ready.connect(self.on_ready)

        n = Note()
        n.string = 4
        n.fret = 0
        n.velocity = 100
        n.duration = 4000
        self.effects_preview_note = n

    def handle_pitch_change_preview_event(self, evt: StringBendEvent):
        self.preview_instr.note_event(self.effects_preview_note)
        self.effects_preview_note.pitch_range = evt.pitch_range 
        self.effects_preview_note.pitch_changes = evt.pitch_changes 
        self.preview_instr.pitchwheel_event(self.effects_preview_note)

    def handle_preview_play(self, n: Note):
        self.preview_instr.note_event(n)
        # self.synth_service.noteon(FRETBOARD_CHANNEL, n.midi_code, n.velocity)

    def handle_effects_preview(self, evt: EffectPreview):
        self.preview_instr.effects_change(evt.changes)
        # send an arbitrary note to hear what applying the effect sounds like.
        self.preview_instr.note_event(self.effects_preview_note)

    def handle_preview_stop(self, n: Note):
        self.preview_instr.note_event(n)
        # self.synth_service.noteoff(FRETBOARD_CHANNEL, n.midi_code)
