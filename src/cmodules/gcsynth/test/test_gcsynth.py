#!/usr/bin/env python

import unittest
import os
import time

import gcsynth


base_dir = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-5])


class TestGcSynth(unittest.TestCase):
    def test_start(self):
        fake_data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
            "test": True
        }
        gcsynth.start(fake_data)

    def test_start_error(self):
        fake_data = {
            "test": True
        }
        success = False
        try:
            gcsynth.start(fake_data)
            
        except gcsynth.GcsynthException:
            print("success, forced an exception and was caght!")   
            success = True
        assert(success)

    def test_start_stop(self):
        data = {
            "sfpaths": [base_dir+"/data/sf/27mg_Symphony_Hall_Bank.SF2"],
        }
        gcsynth.start(data)
        time.sleep(2)
        gcsynth.stop()



if __name__ == '__main__':
    unittest.main()