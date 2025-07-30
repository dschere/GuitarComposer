"""
Central place for custom signals/slots for the application
"""
import queue
from typing import Dict, List, Tuple
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog
from singleton_decorator import singleton

from models.measure import Measure, TabEvent
from models.note import Note
from models.param import EffectParameter
from models.track import Track
from models.effect import Effect, Effects
from models.song import Song
 

#from view.dialogs.effectsControlDialog.dialog import EffectChanges, EffectPreview



class ScaleSelectedEvent:
    def __init__(self):
        self.scale_midi = []
        self.scale_seq = []
        self.key = ""
        self.degrees = None


class ClearScaleEvent:
    pass

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
        self.points = []

class EditorEvent:
    UNINITIALIZED = -1
    ADD_MODEL = 0
    ADD_TRACK_EDITOR = 1
    KEY_EVENT = 2
    TUNING_CHANGE = 3
    MEASURE_CLICKED = 4
    BEND_EVENT = 5
    UNDO_EVENT = 6
    REDO_EVENT = 7

    # applied to the measure at the current moment
    MEASURE_REPEAT_START_KEY = 6
    MEASURE_REPEAT_END_KEY = 7

    def __init__(self, evt_type = -1):
        self.ev_type = evt_type
        self.model : Track | None = None
        self.track_editor = None
        self.key = -1
        self.tuning = None
        self.measure = 1
        self.bend_event : StringBendEvent | None = None  
        self.control_key_pressed = False

class PlayerEvent:
    UNINITIALIZED = -1
    PLAY = 0
    STOP = 1
    SKIP_FORWARD_MEASURE = 2
    SKIP_BACKWARD_MEASURE = 3
    PAUSE = 4
    SETTINGS = 5
    PLAY_CURRENT_MOMENT = 6

    def __init__(self, ev_type = -1):
        self.ev_type = ev_type
        self.tracks : List[Track] = []  
        self.measure_num = -1

@singleton
class MsgSeqCounter:
    def __init__(self):
        self.count = 0

    def get(self):
        r = self.count 
        self.count += 1
        return r

class PlayerVisualEvent:
    TABEVENT_HIGHLIGHT_ON  = 1
    TABEVENT_HIGHLIGHT_OFF = 2


    def __init__(self, ev_type : int, tab_event : TabEvent ):
        self.ev_type = ev_type
        self.tab_event : TabEvent = tab_event
        self.measure : Measure | None = None

global _toolbar_button_update


EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]

class EffectPreview:
    def __init__(self, e :Effects, c: EffectChanges):
        self.effects = e
        self.changes = c
        self.note = "C3"
        self.repeat_note = False
        self.note_interval = 120        

class TrackItem(QStandardItem):
    pass 
class PropertiesItem(QStandardItem):
    pass

class SongItem(QStandardItem):
    pass

class QueryMessage:
    def __init__(self, ident: str, **kwargs):
        self.ident = ident 
        self.kwargs = kwargs
        self.resp_queue = queue.Queue() 

class QueryResult:
    def __init__(self):
        self.track : Track | None = None  
        self.measure_num = -1 
        self.tab_num = -1
                        
@singleton
class _Signals(QObject):
    redo_undo_update = pyqtSignal(Track)
    query_slot = pyqtSignal(QueryMessage) 

    def set_query_reactor(self, ident: str, callback):
        class handler(QObject):
            def __init__(self, ident, cb):
                super().__init__()
                self.cb = cb 
                self.ident = ident 

            def __call__(self, msg: QueryMessage):
                if msg.ident == self.ident:
                    result = self.cb(msg.ident, **msg.kwargs)
                    msg.resp_queue.put(result)

        self.query_slot.connect(handler(ident, callback))

    def query(self, ident: str, **kwargs):
        msg = QueryMessage(ident, **kwargs)
        self.query_slot.emit(msg)
        if 'timeout' in kwargs:
            return msg.resp_queue.get(timeout=kwargs['timeout'])
        return msg.resp_queue.get()

    scale_selected = pyqtSignal(ScaleSelectedEvent)
    clear_scale = pyqtSignal(ClearScaleEvent)
    load_settings = pyqtSignal(QSettings)
    save_settings = pyqtSignal(QSettings)
    preview_play = pyqtSignal(Note)
    preview_stop = pyqtSignal(Note)
    preview_pitch_change = pyqtSignal(StringBendEvent)

    tree_item_added = pyqtSignal(QStandardItem)

    startup = pyqtSignal(object)
    ready = pyqtSignal(object)  # all startup handlers have run app is up.
    shutdown = pyqtSignal(object)

    instrument_selected = pyqtSignal(InstrumentSelectedEvent)

    # menu events
    open_song = pyqtSignal()
    close_song = pyqtSignal()
    new_song = pyqtSignal()
    save_song = pyqtSignal()
    save_as_song = pyqtSignal()

    update_navigator = pyqtSignal(QStandardItemModel)
    fretboard_inst_select = pyqtSignal(object)

    theme_change = pyqtSignal(object)

    editor_event = pyqtSignal(EditorEvent)
    track_update = pyqtSignal(Track)
    song_selected = pyqtSignal(Song)
    
    # route EffectChanges to synth channel(s)
    preview_effect = pyqtSignal(EffectPreview)

    player_event = pyqtSignal(PlayerEvent)
    player_visual_event = pyqtSignal(PlayerVisualEvent)



Signals = _Signals()

