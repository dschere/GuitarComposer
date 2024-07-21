"""
Main controller for application
"""
import pickle
import os

from guitarcomposer.model.song import song as song_model
from guitarcomposer.model.track import track as track_model


class controller:
    def __init__(self):
        self.songs = {}

    def on_before_main_loop(self, mainwin):
        "initialization of sub controllers"
        
        # create a blank score
        name = "noname"
        score_view = mainwin.add_song(name)
        
        # create a blank score
        s_model = song_model()
        t_model = track_model()
        s_model.tracks["guitar1"] = t_model  
        
        score_view.get_editor().render_score(s_model)
        
        # assign blank score to score view
        
        self.songs[name] = score_view
            
