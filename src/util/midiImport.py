"""
Utility that loads and parses midi files. The user can supply a 
filename or a url. 

"""
from typing import List, Tuple

import requests
import tempfile
import os, copy
import collections
import math
from singleton_decorator import singleton

from models.note import Note
from models.track import Track
from music.durationtypes import *
from models.song import Song 
from models.measure import Measure, TabEvent, TimeSig, TupletTypes, TUPLET_DISABLED

from services.synth.synthservice import synthservice


import bisect 

from time import time
import mido

from music.durationtypes import *

from PyQt6.QtCore import QObject, pyqtSignal


class MockTabEvent(TabEvent):
    def __init__(self):
        super().__init__(6)
        self.computed_beats = 0.0


@singleton
class midiDurationClassifier:
    """
    Given only a duration find the least complex nearest match to a 
    note + attributes. So a diration of 0.333 is likely a triplet eight note. 
    """
    def __init__(self):
        # list of mock tab events sorted by duration
        self.mock_te_list = []
        dotted = 1
        double_dotted = 2
        dotCfgCodes = [0, dotted, double_dotted]
        dur_types = [WHOLE, HALF, QUARTER, EIGHTH, SIXTEENTH, THIRTYSECOND, SIXTYFORTH]
        ttypes = list(TupletTypes.keys()) + [TUPLET_DISABLED]
        # make a list of all combinations 
        for duration in dur_types:
            for dcfg in dotCfgCodes: 
                for tupletType in ttypes:
                    te_ref = MockTabEvent()
                    te_ref.duration = duration
                    if dcfg == dotted:
                        te_ref.dotted = True
                    elif dcfg == double_dotted:
                        te_ref.double_dotted = True 
                    te_ref.tuplet_code = tupletType
                    te_ref.computed_beats = te_ref.beats(1.0)

                    self.mock_te_list.append(te_ref)
        self.mock_te_list.sort(key = lambda te: te.computed_beats)

    def find_nearest_match(self, duration) -> TabEvent:
        key_func = lambda item: item.computed_beats 
        idx = bisect.bisect_left(self.mock_te_list, duration, key=key_func)
        if idx == 0:
            return self.mock_te_list[0]
        if idx == len(self.mock_te_list):
            return self.mock_te_list[-1]
        left_obj = self.mock_te_list[idx - 1]
        right_obj = self.mock_te_list[idx]
        
        # Compare distances using the object attributes
        if duration - left_obj.computed_beats <= right_obj.computed_beats - duration:
            return left_obj
        else:
            return right_obj








class track_generator:
    def __init__(self, midi, key_signature, default_timesig):
        self.duration_finder = midiDurationClassifier()
        self.midi = midi
        self.ss = synthservice()

        self.t = Track()
        self.t.instrument_name = self.ss.instrument_name_by_preset(0)

        self.default_bpm = 120 
        self.default_key = key_signature

        self.current_measure = Measure()
        self.current_measure.key = key_signature
        self.current_measure.timesig = default_timesig
            
        self.absolute_time = 0
        self.last_atime = 0

        # time -> list of midi codes and durations.
        self.time_to_notes = collections.OrderedDict()
        self.time_to_meta = collections.OrderedDict()
        # midi code -> 
        self.active_notes = {}
        self.tpb = self.midi.ticks_per_beat

    def getTrack(self):
        return self.t

    def proc_msg(self, msg):
        
        if not msg.is_meta:
            self.absolute_time += msg.time

        # if msg.type == 'key_signature':
        #     self.current_measure.key = msg.key 
        # elif msg.type == 'set_tempo':    
        #     self.current_measure.bpm = mido.tempo2bpm(msg.tempo)
        # elif msg.type == 'program_change':
        #     #print(f"program change {msg.program}")
        #     self.t.instrument_name = self.ss.instrument_name_by_preset(msg.program)

        if msg.type == 'note_on' and msg.velocity > 0:
            # Store the start time using the note number as the key
            self.active_notes[msg.note] = self.absolute_time
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in self.active_notes:
                start_time = self.active_notes[msg.note]
                duration = self.absolute_time - start_time     
                if self.absolute_time not in self.time_to_notes:
                    self.time_to_notes[self.absolute_time] = []
                
                te_ref = self.duration_finder.find_nearest_match(duration)
                self.time_to_notes[self.absolute_time].append((msg.note,te_ref,))
                
                    




class midiSongLoader(QObject):
    """
    Generates a Song object using a midi file.
    """
    EVT_LOG_ERROR = 0
    EVT_LOG_WARN = 1
    EVT_LOG_INFO = 2

    # these would normally be routed to a dialog box so the
    # user has something to see other than a spinner.
    eventLog = pyqtSignal(object)
    duration_classifier = midiDurationClassifier()

    def __init__(self):
        super().__init__()
        self.song = Song() 
        self.midi : mido.MidiFile | None = None
        
        # get the synth singleton
        self.ss = synthservice()

    def parse(self):
        assert(self.midi)

        default_timesig = TimeSig()
        key_signature = 'C'
        tpb = self.midi.ticks_per_beat

        for (tnum,track) in enumerate(self.midi.tracks):
            tgen = track_generator(self.midi, key_signature, default_timesig)
            for msg in track:
                tgen.proc_msg(msg)
            self.song.tracks.append(tgen.getTrack())

    def generate(self):
        self.parse()


    def load_from_file(self, filename, isTempfile=False, url=None) -> bool:
        try:
            self.midi = mido.MidiFile(filename)
        except Exception as e:
            if isTempfile:
                self.eventLog.emit((self.EVT_LOG_ERROR,f"failed to load contents of {url}: {e}"))
            else:
                self.eventLog.emit((self.EVT_LOG_ERROR,f"failed to load midifile {filename}: {e}"))
            return True
        return False


    def download_from_url(self, url) -> bool:
        self.eventLog.emit((self.EVT_LOG_INFO,f"downloading {url}"))
        try:
            r = requests.get(url)
            (fd, filename) = tempfile.mkstemp()
            f = os.fdopen(fd,'w')
            f.write(r.content.decode())
            f.close()
            result = self.load_from_file(filename, True, url)
            os.remove(filename)
            return result
        
        except Exception as e:
            self.eventLog.emit((self.EVT_LOG_ERROR,f"failed to download {url}: {e}"))
            return True


def unittest():
    import sys
    from PyQt6.QtWidgets import QApplication
    import qdarktheme
    from services.synth.synthservice import synthservice
   
    ss = synthservice()
    ss.start()

    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    loader = midiSongLoader()

    loader.eventLog.connect(print)

    loader.load_from_file('/home/david/Downloads/mars-bringer-f-war.mid')
    loader.generate()


if __name__ == '__main__':
    unittest()



