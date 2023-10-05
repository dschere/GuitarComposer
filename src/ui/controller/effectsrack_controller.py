"""
Controller for the effects rack.
"""

from models.effect import Effect, EffectsSchema 
import copy
import atexit

from common.dispatch import DispatchTable, EffectsParamTopic, \
    TOPIC_EFFECTS_RACK_LIVE_START, TOPIC_EFFECTS_RACK_LIVE_STOP, \
    TOPIC_EFFECTS_RACK_DIALOG
from services.liveaudio import LiveAudioPlayer
from ui.dialogs.effectsrack import EffectsRackDialog

class EffectsRackController:
    def __init__(self):
        self.player = None
        
        DispatchTable.subscribe(TOPIC_EFFECTS_RACK_LIVE_START,\
            self.on_start_player)
        DispatchTable.subscribe(TOPIC_EFFECTS_RACK_LIVE_STOP,\
            self.on_stop_player)
        DispatchTable.subscribe(TOPIC_EFFECTS_RACK_DIALOG, \
            self.open_dialog)    
            
        atexit.register(self.on_stop_player)    
        
    def on_start_player(self, topic, obj, data):
        capture_device = "hw:%d" % data['device_number'] 
        model = data['model']
        filename = data['filename']
        if self.player:
            self.player.stop()
        self.player = LiveAudioPlayer(capture_device, model, filename)
        self.player.start()
         
    def on_stop_player(self, *args):
        if self.player:
            self.player.stop()
             
        
    def open_dialog(self, topic, obj, data):
        dialog = EffectsRackDialog()
        dialog.exec()


