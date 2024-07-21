from guitarcomposer.services.fluidsynth.api import fs_api_interface, api


class fs_guitar_api(fs_api_interface):
    # strings from low e to high e 
    STRING1 = 0
    STRING2 = 1
    STRING3 = 2
    STRING4 = 3
    STRING5 = 4
    STRING6 = 5

    STRING1_HARMONIC = 6
    STRING2_HARMONIC = 7
    STRING3_HARMONIC = 8
    STRING4_HARMONIC = 12
    STRING5_HARMONIC = 10
    STRING6_HARMONIC = 11

    STRING1_MUTED = 13
    STRING2_MUTED = 14
    STRING3_MUTED = 15
    STRING4_MUTED = 16
    STRING5_MUTED = 17
    STRING6_MUTED = 18
    
    string_to_harmonic = {
        1: STRING1_HARMONIC,
        2: STRING2_HARMONIC,
        3: STRING3_HARMONIC,
        4: STRING4_HARMONIC,
        5: STRING5_HARMONIC,
        6: STRING6_HARMONIC
    }

    def __init__(self, tuning):
        self.fs_api = api(guitar=True)
        self.tuning = tuning
        self.note_channels = {}

    def start(self):
        """
        The guitar uses a special sound font that dedicates a channel per string.
        """
        self.fs_api.start()
        # the channel # and the instrument # always match
        for chan in range(0,19):
            if chan == 9:
                continue # this is the precusion channel which isn't in this sound font
            self.fs_api.prog(chan, chan)
            

    def stop(self):
        self.fs_api.stop()

    def _legatto_noteoff(self, string):
        # stop playing any note the matches the string
        channels = self.note_channels.get(string, [])
        for (chan,key) in channels:
            self.fs_api.noteoff(chan, key)
        self.note_channels[string] = []
        return []     

    def pitch_bend_range(self, string, semitones):
        channels = self.note_channels.get(string, [])
        for chan in channels:
            self.fs_api.pitch_bend_range(chan, semitones) 

    def clear_pitch_bend(self, string):
        channels = self.note_channels.get(string, [])
        for chan in channels:
            self.fs_api.pitch_bend(chan, 0) 

    def pitch_bend(self, string, val):
        channels = self.note_channels.get(string, [])
        for chan in channels:
            self.fs_api.pitch_bend(chan, val)

    def noteoff(self, fret, string):
        key = self.tuning[string] + fret
        channels = [
            string - 1,
            self.string_to_harmonic[string],  
            string - 1 + self.STRING1_MUTED
        ]
        for chan in channels:
            self.fs_api.noteoff(chan, key)

    def noteon(self, fret, string, velocity, **effects):
        muted_weighting = effects.get('muted',0.0)
        harmonic_weighting = effects.get('harmonic',0.0)
        note_weighting = effects.get('note_weighting', 1.0)
        channels = self._legatto_noteoff(string)
        key = self.tuning[string] + fret

        t = muted_weighting + harmonic_weighting + note_weighting
        note_vel =  (note_weighting / t) * velocity
        if note_vel > 0:
            # each guitar string mapped to a channel
            chan = string - 1
            self.fs_api.noteon(chan, key, note_vel)
            channels.append((chan,key))

        harmonic_vel = (harmonic_weighting / t) * velocity
        if harmonic_vel > 0:
            # harmonics 
            chan = self.string_to_harmonic[string]
            self.fs_api.noteon(chan, key, harmonic_vel)
            channels.append((chan,key))

        muted_vel = (muted_weighting / t) * velocity
        if muted_vel > 0:
            # muted strings
            chan = string - 1 + self.STRING1_MUTED
            self.fs_api.noteon(chan, key, muted_vel)
            channels.append((chan,key))

        # record noteon events for this guitar string
        self.note_channels[string] = channels    
