""" 
The sequencer plots all music events throughout the song for
all instruments.
"""
import sched
import time

class sequence_entry:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.func(*self.args, **self.kwargs)    

class track_sequence:
    def __init__(self, s):
        self.s = s

        self.lagato = False
        self.staccato = False
    
    def _add_note(self, te, fs_interface):
        """ performs a noteon + effects 
        """
        _muted = 0.0
        _harmonic = 0.0
        _note_weighting = 1.0
        if te.muted:
            _muted = te.muted
        elif te.harmonic:
            if te.harmonic["natural"]:
                _harmonic = 1.0
                _note_weighting = 0.0
                _muted = 0.0
            elif te.harmonic["pinched"]:
                _harmonic = 0.4
                _note_weighting = 0.4
                _muted = 0.20
            elif te.harmonic["semi"]:
                _harmonic = 0.3
                _note_weighting = 0.7
                _muted = 0.0

        # schedule note on
        se_noteon = sequence_entry(
            fs_interface.noteon, 
            te.fret, te.g_string, te.dynamic,
            muted=_muted, harmonic=_harmonic, note_weighting=_note_weighting
        )
        self.s.enter(te.time_pos, 1, se_noteon)
        
        # schedule pitch bends
        # te.bend = {} # decimal percentage of n.duration -> pitch bend in steps  
        if te.bend:
            for dur_perentage, value in te.bend.items():
                t = te.time_pos + (dur_perentage * te.duration)
                # def pitch_bend(self, string, vel):
                self.s.enter(t, 1, sequence_entry(
                    fs_interface.pitch_bend, 
                    te.g_string, value
                ))

        # schedule a noteoff 
        se_noteof = sequence_entry(fs_interface.noteoff, te.fret, te.g_string)
        if self.stacatto:
            self.s.enter(te.time_pos + (te.duration/2), 1, se_noteof)
        elif self.lagato:    
            pass # do not schedule a noteoff
        else:
            self.s.enter(te.time_pos + te.duration, 1, se_noteof)

    def _add_chord(self, te, fs_interface):
        """
        Play a chord. 
        """
        if te.stroke_duration:
            n_indexes = list(range(0,len(te.notes)))
            if te.stroke == "up":
                n_indexes.reverse()
            first_note = True

            for i in n_indexes:
                note = te.notes[i]
                t = te.time_pos + ((float(i)/len(n_indexes)) * te.stroke_duration)
                d = note.dynamic
                if first_note and d < 117:
                    first_note = False
                    d += 10
                se_noteon = sequence_entry(
                    fs_interface.noteon, note.fret, note.g_string, note.dynamic)
                self.s.enter(t, 1, se_noteon)
        else:
            for note in te.notes:
                se_noteon = sequence_entry(
                    fs_interface.noteon, note.fret, note.g_string, note.dynamic)
                self.s.enter(te.time_pos, 1, se_noteon)

        if te.stroke_duration > te.duration:
            t = te.time_pos + te.stroke_duration
        else:    
            t = te.time_pos + te.duration 
        if self.stacatto:
            t = te.time_pos + (te.duration/2)
        elif self.lagato:
            t = -1
        if t != -1:
            for note in te.notes:
                se_noteoff = sequence_entry(
                    fs_interface.noteoff, note.fret, note.g_string)
                self.s.enter(t, 1, se_noteoff)


    def add(self, te, fs_interface):
        """
        record actions at a specific time to perform note on/off 
        and pitch bend events. 
        """
        name = te.__class__.__name__
        if name == 'command':
            self.lagato = te.lagato
            self.stacatto = te.stacatto
        elif name == 'note':
            self._add_note(te, fs_interface)
        elif name == 'chord':
            self._add_chord(te, fs_interface)
        

class sequencer:
    def __init__(self):
        self.sched = sched.scheduler(time.time, time.sleep)

    def run(self):
        self.sched.run()

    def process(self, track, fs_interface):
        ts = track_sequence(self.sched)
        for te in track.events:
            ts.add(te, fs_interface)
