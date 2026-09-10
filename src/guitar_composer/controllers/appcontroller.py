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

from guitar_composer.models.effect import Effect
from guitar_composer.models.note import Note
from guitar_composer.models.song import Song
from guitar_composer.models.track import Track
from guitar_composer.view.events import Signals, StringBendEvent
from guitar_composer.services.projectMngr import ProjectManager
from guitar_composer.music.instrument import Instrument
from guitar_composer.view.config import LabelText

from guitar_composer.view.dialogs.effectsControlDialog.dialog import EffectPreview,\
    EffectChanges
from guitar_composer.view.dialogs.TrackPropertiesDialog import TrackPropertiesDialog

from guitar_composer.view.events import Signals, TrackItem, PropertiesItem, SongItem, InstrumentSelectedEvent

from guitar_composer.view.dialogs.msgboxes import alert

from guitar_composer.view.dialogs.importDialog import ImportDialog



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
        """Open an existing song file from the project repository or via file dialog."""
        saved_song = ProjectManager().open_song_using_title(self.song.title)
        if not saved_song:
            saved_song = ProjectManager().open_song_using_dialog()
            
        if saved_song:
            self.song = saved_song


    def __init__(self, title):
        """Initialize a SongController instance managing the given song title and connect signal listeners."""
        self.song = Song()
        self.song.title = title
        self.q_model = None

        Signals.track_update.connect(self.on_track_change)
        Signals.open_song.connect(self.open_song)

    def __del__(self):
        """Disconnect signal listeners upon controller destruction."""
        try:
            Signals.open_song.disconnect(self.open_song)
            Signals.track_update.disconnect(self.on_track_change)
        except RuntimeError:
            # Possible that Signals has been deleted. 
            pass

    def setTitle(self, title):
        """Set the managed song title.

        Args:
            title: String song title.
        """
        self.song.title = title

    def getTitle(self):
        """Return the managed song title."""
        return self.song.title

    def load_model(self, s: Song):
        """Load a new Song model into this controller.

        Args:
            s: Song instance.
        """
        self.song = s

    def save_model(self, allow_dialog=False):
        """Persist the managed song model to storage.

        Args:
            allow_dialog: True to prompt with file save dialog if unassigned.
        """
        if isinstance(self.song, Song):
            ProjectManager().save_song(self.song, allow_dialog)

    def title(self):
        """Return the managed song title string."""
        return self.song.title

    def addQTrackModel(self, track, root):
        """Construct and insert QStandardItem tree items for a track and its properties.

        Args:
            track: Track model instance.
            root: Parent QStandardItem node.
        """
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
        """Add a default guitar track to the song tree triggered by user UI action."""
        if not self.q_model:
            logging.error("userAddTrack called but we have not setup model!")
            return

        track = self.addTrack('12-str.GT')
        self.addQTrackModel(track, self.q_model)

    def addTrack(self, instr_name):
        """Instantiate and append a new Track with the specified instrument name to the song.

        Args:
            instr_name: Instrument identifier string.

        Returns:
            The created Track instance.
        """
        # build data structure
        track = Track()
        track.instrument_name = instr_name
        self.song.tracks.append(track)

        return track
    
    
    def addTrackFromDialog(self) -> Track | None:
        """Display the TrackPropertiesDialog and return a configured Track upon confirmation."""
        track = Track()
        tpd = TrackPropertiesDialog(None, track)
        r = tpd.exec()
        if r == 1:
            # user select OK, return populated track
            return track

    def removeTrack(self, instr_name):
        """Remove a track by instrument name from the song."""
        # TODO, must add checkin/checkout capability to the
        # channel manager in the synth service.
        pass

    def getSong(self):
        """Return the managed Song instance."""
        return self.song

def log_model_contents(model: QStandardItemModel):
    """Log the hierarchical contents and display roles of a QStandardItemModel for debugging.

    Args:
        model: QStandardItemModel to inspect.
    """
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
        """Handle tree item label edits to rename songs while validating against duplicate titles.

        Args:
            item: QStandardItem whose title text changed.
        """
        if not isinstance(item.data(), Song):
            return

        new_title = item.text()
        song_inst : Song = item.data()

        if new_title in self.song_ctrl:
            potential_dup = self.song_ctrl[new_title]
            if potential_dup is not song_inst:
                # this is a dup then we already have a song with that title
                QMessageBox.critical(None,
                    "Error", f"{new_title} song title already in use by another song!",
                        QMessageBox.StandardButton.Ok)
                return
        
        sc = self.song_ctrl[song_inst.title]
        del self.song_ctrl[song_inst.title]
        song_inst.title = new_title
        self.song_ctrl[song_inst.title] = sc

    def upsert_song_to_navigator(self, song: Song):
        """
        add or replace a song in the navigator
        """
        # update song_ctrl then call update navigator to build
        # a new model.
        existing_sc = None 
        for sc in self.song_ctrl.values():
            if sc.song.filename == song.filename:
                existing_sc = sc 
            elif sc.song.title == song.title:
                msg = f"Song {sc.song.filename} has the same title, it will be closed"
                sc.save_model()
                alert(msg)

        if existing_sc:
            existing_sc.load_model(song) 
        else:
            sc = SongController(song.title)
            sc.load_model(song)
            self.song_ctrl[song.title] = sc

        self.update_navigator(selected=song)

    def on_open_song(self):
        """ handle open song signal from mainwin """
        s = ProjectManager().open_song_using_dialog()
        if s is not None:
            self.upsert_song_to_navigator(s)  

    def on_midi_load_dialog(self):
        """Display the MIDI import dialog."""
        import_dialog = ImportDialog()
        import_dialog.exec()

    def update_navigator(self, **kw_args):
        "construct a QModel for the treeView"
        root = QStandardItemModel()
        root.itemChanged.connect(self.on_song_title_changed)
        root.setHorizontalHeaderLabels(["Composition"])
        selected = kw_args.get('selected')

        for title in sorted(self.song_ctrl):
            sc = self.song_ctrl[title]
            if not selected:
                selected = sc.song 
                
            song_item = sc.createQModel()
            root.appendRow(song_item)

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            titles = sorted(self.song_ctrl)
            logging.debug("setup controllers for %s" % str(titles))
            log_model_contents(root)

        # send to navigator widget
        Signals.update_navigator.emit(root)
        Signals.song_selected.emit(selected)

    def delete_track(self, evt):
        """Prompt user confirmation and remove the requested track from the song.

        Args:
            evt: Event specifying song and track to delete.
        """
        if len(evt.song.tracks) == 1:
            return

        reply = QMessageBox.question(
            None,
            "Confirmation",
            f"Are you sure you want to delete the track {evt.track.instrument_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No # Default button
        )

        if reply == QMessageBox.StandardButton.Yes:
            index = evt.song.tracks.index(evt.track)
            del evt.song.tracks[index]
            self.update_navigator()


    def add_track(self, song_title = None):
        """Display track creation dialog and synchronize measure structure with existing tracks.

        Args:
            song_title: Optional title of target song (defaults to current song).
        """
        sc : SongController | None = self.song_ctrl.get(song_title, self.current_song)
        if sc is not None:
            track = sc.addTrackFromDialog()
            if track is not None:
                if len(sc.song.tracks) > 0:
                    ref_track = sc.song.tracks[0]
                    track.sync_measure_structure(ref_track)

                sc.song.tracks.append(track)
                self.update_navigator()
              
    def on_ready(self, app):
        """Initialize workspace upon startup by opening saved projects or creating a default starter song.

        Args:
            app: QApplication instance.
        """
        # setup navigator, score editor
        titles = self.projects.titles()

        if len(titles) == 0:
            sc = SongController("noname")
            sc.addTrack('12-str.GT')
            self.song_ctrl[sc.title()] = sc
            self.current_song = sc

        else:
            for title in titles:
                song_model = self.projects.open_song_using_title(title)
                sc = SongController(title)
                sc.load_model(song_model)
                self.song_ctrl[sc.title()] = sc
                self.current_song = sc

        self.update_navigator()

    def on_load_settings(self, settings: QSettings):
        """Load persisted active song titles from application settings.

        Args:
            settings: QSettings instance.
        """
        if settings.contains(self.settings_key):
            val = settings.value(self.settings_key)
            self.active_song_titles = set(json.loads(val))

    def on_save_settings(self, settings: QSettings):
        """Persist active song titles into application settings.

        Args:
            settings: QSettings instance.
        """
        val = json.dumps(list(self.active_song_titles))
        settings.setValue(self.settings_key, val)

    def on_preview_instr_changed(self, instrument_name):
        """Reinitialize the preview instrument with the newly selected instrument name.

        Args:
            instrument_name: Name of instrument to load for previews.
        """
        self.preview_instr.free_resources()
        self.preview_instr = Instrument(instrument_name)

    def on_save_song(self):
        """ saves all opened songs.
        """
        for (title,sc) in self.song_ctrl.items():
            try:
                self.projects.save_song(sc.song)
            except Exception as e:
                alert(str(e), title=type(e).__name__)

    def on_close_song(self, title):
        """Prompt to save and close the song specified by title, updating navigation selection.

        Args:
            title: Title string of song to close.
        """
        sc : SongController | None = self.song_ctrl.get(title)
        if sc is not None:
            reply = QMessageBox.question(
                None,
                "Confirmation",
                f"Should I save '{title}' before I close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No # Default button
            )
            if reply == QMessageBox.StandardButton.Yes:
                sc.save_model()

            # remove from project manager so it doesn't auto load
            self.projects.close_song(sc.getSong())

            update_current_song = False
            if self.current_song == self.song_ctrl[title]:
                update_current_song = True

            del self.song_ctrl[title]

            if len(self.song_ctrl) == 0:
                self.on_new_song()
            else:
                if update_current_song:
                    titles = list(self.song_ctrl.keys())
                    titles.sort()
                    new_sc = self.song_ctrl[titles[0]]
                    self.current_song = new_sc
                    self.current_track = new_sc.getSong().tracks[0]            

                self.update_navigator()


            

    def on_new_song(self):
        """Create a new untitled composition with a default guitar track and display it in navigator."""
        self.noname_counter += 1
        sc = SongController(f"noname-{self.noname_counter}")
        sc.addTrack('12-str.GT')
        self.song_ctrl[sc.title()] = sc
        self.current_song = sc
        self.current_track = sc.song.tracks[0]
        self.update_navigator()

    def __init__(self, synth_service):
        """Initialize the AppController, set up project management, preview instruments, and signal bindings.

        Args:
            synth_service: SynthService instance.
        """
        self.synth_service = synth_service
        self.editor_ctrl = None
        self.noname_counter = 0
        

        self.projects = ProjectManager()
        self.active_song_titles = set()
        self.song_ctrl = {}
        self.preview_instr = Instrument("12-str.GT")
        Signals.fretboard_inst_select.connect(self.on_preview_instr_changed)

        # current track being edited.
        self.current_track = None
        self.current_song = None

        Signals.preview_play.connect(self.handle_preview_play)
        Signals.preview_stop.connect(self.handle_preview_stop)
        Signals.preview_effect.connect(self.handle_effects_preview)
        Signals.preview_pitch_change.connect(self.handle_pitch_change_preview_event)

        Signals.load_settings.connect(self.on_load_settings)
        Signals.save_settings.connect(self.on_load_settings)

        Signals.ready.connect(self.on_ready)
        Signals.save_song.connect(self.on_save_song)
        Signals.open_song.connect(self.on_open_song)
        Signals.close_song.connect(self.on_close_song)
        Signals.new_song.connect(self.on_new_song)
        Signals.midi_load_dialog.connect(self.on_midi_load_dialog)
        Signals.imported_song.connect(self.upsert_song_to_navigator)

        Signals.add_track.connect(self.add_track)
        Signals.delete_track.connect(self.delete_track)
        

        n = Note()
        n.string = 4
        n.fret = 0
        n.velocity = 100
        n.duration = 4000
        n.midi_code = 57

        self.effects_preview_note = n

    def handle_pitch_change_preview_event(self, evt: StringBendEvent):
        """Audition string bend pitch curve changes using the preview instrument.

        Args:
            evt: StringBendEvent containing curve points and pitch range.
        """
        self.preview_instr.note_event(self.effects_preview_note)
        self.effects_preview_note.pitch_range = evt.pitch_range 
        self.effects_preview_note.pitch_changes = evt.pitch_changes 
        self.preview_instr.pitchwheel_event(self.effects_preview_note)

    def handle_preview_play(self, n: Note):
        """Play a preview note on the preview instrument.

        Args:
            n: Note to play.
        """
        self.preview_instr.note_event(n)
        # self.synth_service.noteon(FRETBOARD_CHANNEL, n.midi_code, n.velocity)

    def handle_effects_preview(self, evt: EffectPreview):
        """Apply temporary effect changes and audition with a preview note.

        Args:
            evt: EffectPreview containing effect changes.
        """
        self.preview_instr.effects_change(evt.changes)
        # send an arbitrary note to hear what applying the effect sounds like.
        self.preview_instr.note_event(self.effects_preview_note)

    def handle_preview_stop(self, n: Note):
        """Stop note sounding on the preview instrument.

        Args:
            n: Note to silence.
        """
        self.preview_instr.note_event(n)
        # self.synth_service.noteoff(FRETBOARD_CHANNEL, n.midi_code)
