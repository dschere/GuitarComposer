import time, copy

from models.song import Song
from models.track import Track

from music.instrument import Instrument
from view.editor.trackEditorView import TrackEditorView
from view.events import Signals, EditorEvent, PlayerEvent
from services.player import PlayMoment, Player

class PlayerController:
    """ 
    Listens to events from Signals and controls a service.player object.
    """

    def _handle_editor_event(self, evt : EditorEvent):
        if evt.ev_type == EditorEvent.ADD_MODEL:
            assert(evt.model)
            self.current_track = evt.model
            iname = self.current_track.instrument_name
            self.current_instr = Instrument(iname, self.current_track.tuning)

        elif evt.ev_type == EditorEvent.ADD_TRACK_EDITOR:
            self.track_editor = evt.track_editor     

    def _handle_song_selected(self, song: Song):
        self.current_song = song

    def _handler_player_event(self, evt: PlayerEvent):
        if evt.ev_type == PlayerEvent.PLAY_CURRENT_MOMENT:
            self.play_current_moment()
        elif evt.ev_type == PlayerEvent.PLAY:
            self.play() 
            
    def __init__(self):
        self.current_song = None  
        self.current_track : Track | None = None
        self.current_instr : Instrument | None = None
        self.track_editor : TrackEditorView | None = None
        
        Signals.editor_event.connect(self._handle_editor_event)
        Signals.song_selected.connect(self._handle_song_selected)
        Signals.player_event.connect(self._handler_player_event)
        
    def on_song_selected(self, song: Song):
        self.current_song = song 

    def on_track_selected(self, track: Track):
        self.current_track = track

    def play_tracks(self, selected_tracks):
        pass 

    def play(self):
        """
        Mockup for now
        """
        if self.current_song:
            p = Player(self.current_song.tracks)
            p.play()

    def stop(self):
        pass

    def play_current_moment(self):
        if self.current_track and self.current_instr:
            PlayMoment(self.current_track, self.current_instr)
