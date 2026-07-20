"""
Utility that loads and parses midi files. The user can supply a 
filename or a url. 

"""
from typing import List

import requests
import pretty_midi
import tempfile
import os, copy

from models.note import Note
from models.track import Track
from music.durationtypes import *
from models.song import Song 
from models.measure import Measure, TabEvent, TimeSig, TupletTypes

from services.synth.synthservice import synthservice

from tuttut.logic.tab import Tab
from tuttut.logic.theory import Tuning
import argparse
import traceback
from time import time
import numpy as np
from pathlib import Path
np.seterr(divide="ignore")

from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal

class midiImport(QObject):
    info_msg = pyqtSignal(str)
    error_msg = pyqtSignal(str)

    def __init__(self, **config):
        self.song = Song()
        default_weights = {'b': 1, 'height': 1, 'length': 1, 'n_changed_strings': 1}
        self.weights = config.get('weights', default_weights)
        self.midi_tuning = config.get('midi_tuning',["E4", "B3", "G3", "D3", "A2", "E2"])


    def download(self, url):
        try:
            r = requests.get(url)
        except Exception as e:
            msg = f"Unable to download {url}: {e}"
            self.error_msg.emit(msg)
            return
        
        (fd, filename) = tempfile.mkstemp()
        if os.write(fd, r.content) != len(r.content):
            msg = f"io error unable to write {url} content to disk!"
            self.error_msg.emit(msg)
            os.close(fd)
            return

        try:
            self.load(filename)
        except Exception as e:
            msg = f"error while processing {url} content"
            self.error_msg.emit(msg)

        os.close(fd)
        os.remove(filename)

    def generate(self):
        for measure in self.score_tabature.tab["measures"]:
            for ievent, event in enumerate(measure["events"]):
                if "notes" in event:
                    te = TabEvent(6)
                    for note in event["notes"]:
                        string, fret = note["string"], note["fret"]
                        te.fret[string] = fret

                        te.duration = measure["events"][ievent + 1]["measure_timing"] if ievent < len(measure["events"]) - 1 else 1.0
                        print(f"{te.fret} {te.duration}")

        """
        # self is self.score_tabature 
            res = []
    for string in self.tuning.strings:
      header = string.degree
      header += "||" if len(header)>1 else " ||"
      res.append(header)

    for measure in self.tab["measures"]:
      for ievent, event in enumerate(measure["events"]):
        if "notes" in event:
          for note in event["notes"]:
            string, fret = note["string"], note["fret"]
            res[string] += str(fret)

          next_event_timing = measure["events"][ievent + 1]["measure_timing"] if ievent < len(measure["events"]) - 1 else 1.0
          dashes_to_add = max(1, math.floor((next_event_timing - event["measure_timing"]) * 16))

          res = fill_measure_str(res)

          for istring in range(self.nstrings):
            res[istring] += "-" * dashes_to_add

      for istring in range(self.nstrings):
        res[istring] += "|"

        """

    def load(self, filename):
        p = Path(filename).as_posix()
        f = pretty_midi.PrettyMIDI(p)
        tuning = Tuning(self.midi_tuning)
        self.score_tabature = Tab(filename, tuning, f, weights=self.weights)
        self.generate()

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    mi = midiImport()
    mi.load("/home/david/Downloads/time_in_a_bottle.mid")


