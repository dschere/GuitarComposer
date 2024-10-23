import unittest
import os
import time
import json
import sys
import copy
import atexit
import logging
import gcsynth

from music.instrument import *
from models.note import Note
from services.synth.synthservice import synthservice 


def setup_logger():
    fmt = "%(asctime)s %(thread)d %(filename)s:%(lineno)d %(levelname)s\n`"
    fmt += "- %(message)s"
    loglevel = "DEBUG"
    if not hasattr(logging, loglevel):
        print("Warning: undefined LOGLEVEL '%s' falling back to DEBUG!" % loglevel)
        loglevel = 'DEBUG'
    logging.basicConfig(stream=sys.stdout,
                        format=fmt,
                        level=getattr(logging, loglevel)
                        )


setup_logger()


synth = synthservice()
synth.start()
atexit.register(synth.stop)



class TestInstruments(unittest.TestCase):
    def test_1_pick_multi_as_opposed_single(self):
        instr = Instrument("Acoustic Guitar")
        assert(isinstance(instr.implementation, MultiInstrumentImp))

    def test_2_pick_single(self):
        instr = Instrument("Violin")
        assert(isinstance(instr.implementation, SingleInstrumentImp))

    def test_3_play_single(self):

        instr = Instrument("Violin")
        n = Note()        
        n.fret = 3
        n.string = 5
        n.duration = 2000
        n.velocity = 80
        instr.note_event(n)
        time.sleep(3)
        

    def test_4_play_complex(self):

        instr = Instrument("Acoustic Guitar")
        n = Note()        
        n.fret = 3
        n.string = 5
        n.duration = -1
        n.velocity = 120
        instr.note_event(n)

        n = Note()        
        n.fret = 2
        n.string = 4
        n.duration = -1
        n.velocity = 120
        instr.note_event(n)

        n = Note()        
        n.fret = 0
        n.string = 3
        n.duration = -1
        n.velocity = 120
        instr.note_event(n)

        time.sleep(2)
        