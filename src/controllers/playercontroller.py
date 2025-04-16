import time

from models.song import Song
from models.track import Track


class PlayerController:
    """ 
    Listens to events from Signals and controls a service.player object.

    """
    def __init__(self):
        self.current_song = None  
        self.current_track = None
        
    def on_song_selected(self, song: Song):
        self.current_song = song 

    def on_track_selected(self, track: Track):
        self.current_track = track

    def play_tracks(self, selected_tracks):
        pass 

    def play(self):
        pass 

    def stop(self):
        pass