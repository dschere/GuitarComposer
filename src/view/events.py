"""
Central place for custom signals/slots for the application
"""
from typing import List
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from PyQt6.QtCore import Qt
from singleton_decorator import singleton

from models.note import Note
from models.track import Track
from models.effect import Effects
from models.song import Song
from view.dialogs.effectsControlDialog.effectsControls import EffectChanges, EffectPreview


class ScaleSelectedEvent:
    def __init__(self):
        self.scale_midi = []
        self.scale_seq = []
        self.key = ""
        self.degrees = None


class ClearScaleEvent:
    pass


class NewSongEvent:
    pass


class CloseSongEvent:
    pass


class OpenSongEvent:
    def __init__(self):
        self.filename = None


class SaveSongEvent:
    def __init__(self):
        self.filename = None


class InstrumentSelectedEvent:
    def __init__(self):
        self.track = None
        self.instrument = ""

class StringBendEvent:
    def __init__(self):
        # [(when_r,pitch),...]
        # when_r -> time = (self.pitch_range * when_r)   
        self.pitch_changes = []
        self.pitch_range = 2
        self.channel = 0
        self.preview = True

class EditorEvent:
    UNINITIALIZED = -1
    ADD_MODEL = 0
    ADD_TRACK_EDITOR = 1
    KEY_EVENT = 2
    TUNING_CHANGE = 3
    MEASURE_CLICKED = 4
    BEND_EVENT = 5

    def __init__(self):
        self.ev_type = self.UNINITIALIZED
        self.model = None
        self.track_editor = None
        self.key = -1
        self.tuning = None
        self.measure = 1
        self.bend_event : StringBendEvent | None = None  


class PlayerEvent:
    UNINITIALIZED = -1
    PLAY = 0
    STOP = 1
    SKIP_FORWARD_MEASURE = 2
    SKIP_BACKWARD_MEASURE = 3
    PAUSE = 4
    SETTINGS = 5

    def __init__(self):
        self.ev_type = self.UNINITIALIZED
        self.tracks : List[Track] = []  
        self.measure_num = -1

class PlayerVisualEvent:
    def __init__(self, track, measure):
        self.track = track 
        self.measure = measure        

global _toolbar_button_update


@singleton
class _Signals(QObject):
    preview_pitch_change = pyqtSignal(StringBendEvent)
    scale_selected = pyqtSignal(ScaleSelectedEvent)
    clear_scale = pyqtSignal(ClearScaleEvent)
    load_settings = pyqtSignal(QSettings)
    save_settings = pyqtSignal(QSettings)
    preview_play = pyqtSignal(Note)
    preview_stop = pyqtSignal(Note)
    preview_pitch_change = pyqtSignal(StringBendEvent)

    startup = pyqtSignal(object)
    ready = pyqtSignal(object)  # all startup handlers have run app is up.
    shutdown = pyqtSignal(object)

    instrument_selected = pyqtSignal(InstrumentSelectedEvent)

    open_song = pyqtSignal(OpenSongEvent)
    close_song = pyqtSignal(CloseSongEvent)
    new_song = pyqtSignal(NewSongEvent)
    save_song = pyqtSignal(SaveSongEvent)

    update_navigator = pyqtSignal(QStandardItemModel)
    fretboard_inst_select = pyqtSignal(object)

    theme_change = pyqtSignal(object)

    editor_event = pyqtSignal(EditorEvent)
    track_update = pyqtSignal(Track)
    
    # route EffectChanges to synth channel(s)
    preview_effect = pyqtSignal(EffectPreview)

    player_event = pyqtSignal(PlayerEvent)
    player_visual_event = pyqtSignal(PlayerVisualEvent)

Signals = _Signals()