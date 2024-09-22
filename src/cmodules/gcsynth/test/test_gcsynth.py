#!/usr/bin/env python

import unittest
import os

import gcsynth

class TestGcSynth(unittest.TestCase):
    def test_start(self):
        fake_data = {
            "sfpaths": ["../../../../data/sf/27mg_Symphony_Hall_Bank.SF2"],
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
            print("success error caught")   
            success = True
        assert(success)    

if __name__ == '__main__':
    unittest.main()