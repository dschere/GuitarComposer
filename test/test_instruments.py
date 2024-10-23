import unittest
import os
import time
import json
import sys
import copy

import gcsynth

from music.instrument import *


class TestInstruments(unittest.TestCase):
    def test_1_pick_multi_as_opposed_single(self):
        print("entering test ")
        instr = Instrument("Acoustic Guitar")
        assert(isinstance(instr.implementation, MultiInstrumentImp))
        print("test_1_pick_multi_as_opposed_single worked")
