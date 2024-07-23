from guitarcomposer.services.fluidsynth.api import fs_api_interface, api

from singleton_decorator import singleton

@singleton
class fs_default_api:
    """ multi instrument soundfont  
    """
    def __init__(self):
        self.drum_tracks = set()
        self.trackid2chan = {}
        self.trackid2tuning = {}
        self.free_channel = 0
        self.drum_channel = 9
        self.fs_api = api()

    def start(self):
        self.fs_api.start()
        
    def stop(self):
        self.fs_api.stop()        

    def _get_channel(self, track_id):
        if track_id in self.drum_tracks:
            return self.drum_channel
        return self.trackid2chan[track_id]  

    def _assign_channel(self, track_id, midi_code, tuning):
        "track string identifier, midi instrument code"
        if midi_code == 9:
            # channel 9 is reserved for precusion
            self.drum_tracks.add(track_id)
        else:
            self.trackid2chan[track_id] = self.free_channel
            self.trackid2tuning[track_id] = tuning

            self.fs_api.prog(self.free_channel, midi_code)
            self.free_channel += 1
            if self.free_channel == self.drum_channel:
                # skip over drum channel
                self.free_channel += 1


    def instrument_agent(self, track_id, midi_code, tuning):
        """ allocate a channel for this track. associate a track id with 
            a channel and a tuning. return a commin interface for 
            usage. 
        """
        self._assign_channel(track_id, midi_code, tuning)
        class agent(fs_api_interface):
            def __init__(self, inst, track_id):
                super().__init__()
                self.track_id = track_id
                self.inst = inst
            def noteon(self, fret, string, vel):
                self.inst.noteon(self.track_id, fret, string, vel)
            def noteoff(self, track_id, fret, string):
                self.inst.noteoff(self.track_id, fret, string)
            def pitch_bend_range(self, string, semitones):
                self.inst.pitch_bend_range(self.track_id, semitones)
            def pitch_bend(self, string, vel):
                self.inst.pitch_bend(self.track_id, vel)
            def clear_pitch_bend(self, string):
                self.inst.pitch_bend(self.track_id,0)

        return agent(self, track_id) 
        
    def noteon(self, track_id, fret, string, vel):
        key = self.trackid2tuning[track_id][string] + fret
        self.fs_api.noteon(self._get_channel(track_id), key, vel)

    def noteoff(self, track_id, fret, string):
        key = self.trackid2tuning[track_id][string] + fret
        self.fs_api.noteoff(self._get_channel(track_id), key)

    def pitch_bend_range(self, track_id, semitones):
        self.fs_api.pitch_bend_range(self._get_channel(track_id), semitones)

    def pitch_bend(self, track_id, vel):
        self.fs_api.pitch_bend(self._get_channel(track_id), vel)

# todo unit tests