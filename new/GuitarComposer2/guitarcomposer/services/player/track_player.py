"""
This module uses multiple fluidsynth processes to play a set 
tracks.

The guitar is given a separate fluid synth process each string 
a separate channel.

All other instruments are played using a single fluidsynth
process.

All use the TCP interface.
"""

import guitarcomposer.common.midi_instrument_codes as ins_codes
import guitarcomposer.common.resources as RES
from guitarcomposer.services.fluidsynth.fs_guitar_api import fs_guitar_api
from guitarcomposer.services.fluidsynth.fs_default_api import fs_default_api

from guitarcomposer.services.fluidsynth.sequencer import sequencer


class player:
    def __init__(self):
        self.fluidsynth_workers = {}
        # sparce matrix <time> -> list of events
        self.sequencer = sequencer()
        

    def play(self, tracks):
        guitar_fs_list = set()
        fs_default = None

        # analyze tracks determine resources needed to play them.
        for (tid,track) in tracks.items():
            if track.ins.midi_program == ins_codes.ACOUSTIC_STEEL_GUITAR:
                self.fluidsynth_workers[tid] = fs_guitar_api(track.tuning)
                self.fluidsynth_workers[tid].start()
                guitar_fs_list.add(self.fluidsynth_workers[tid])
            else:
                if not fs_default:
                    fs_default = fs_default_api()
                    fs_default.start()
                ins_code = track.ins.midi_program    
                interface = fs_default_api.instrument_agent(tid,ins_code,track.tuning)
                self.fluidsynth_workers[tid] = interface

        # generate a sequence of fluid synth events for all the tracks.
        for (tid,track) in tracks.items():
            fs = self.fluidsynth_workers[tid]
            self.sequencer.process(track, fs)
            
        # play sequence
        self.sequencer.run()

        # stop resources
        for interface in guitar_fs_list:
            interface.stop()
        if fs_default:    
            fs_default.stop()   



