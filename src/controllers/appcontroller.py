"""
High level controller for the main window

"""
from PyQt6.QtCore import QTimer


from models.note import Note
from view.events import Signals


class AppController:

    def __init__(self, synth_service):

        self.synth_service = synth_service
        # current track being edited.
        self.current_track = None

        Signals.preview_play.connect(self.handle_preview_play)
        Signals.preview_stop.connect(self.handle_preview_stop)

    def handle_preview_play(self, n: Note):
        if self.current_track:
            pass
        else:
            self.synth_service.noteon(0, n.midi_code, n.velocity)

    def handle_preview_stop(self, n: Note):
        if self.current_track:
            pass
        else:
            self.synth_service.noteoff(0, n.midi_code)
