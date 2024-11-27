import os
import xml.etree.ElementTree as ET
from singleton_decorator import singleton

from util.midi import midi_codes
from pip._vendor.pyparsing.core import Optional

SCALE_XML_DB = os.environ['GC_BASE_DIR']+"/data/music_theory/scales.xml"


@singleton
class MusicScales:
    def __init__(self):
        self.scales = {}
        self.degrees = {}
        tree = ET.parse(SCALE_XML_DB)
        root = tree.getroot()
        for scale in root:
            n = scale.attrib['name'].lower()
            keys = [int(k) for k in scale.attrib['keys'].split(',')]
            self.scales[n] = keys
            if 'degrees' in scale.attrib:
                deg = scale.attrib['degrees'].split(',')
                self.degrees[n] = deg

        self.sorted_names = sorted(self.scales)

    def getDegreeLabels(self, _scale_name: str): # type: ignore
        degrees = None 
        scale_name = _scale_name.lower()
        if scale_name in self.degrees:
            degrees = self.degrees[scale_name]

        return degrees # type: ignore

    def generate_midi_scale_codes(self, _scale_name, key):
        scale_name = _scale_name.lower()
        if scale_name not in self.scales:
            raise ValueError("Unknown scale '%s'" % scale_name)

        key_mc = midi_codes.midi_code(key+"0")
        s = self.scales[scale_name]
        mc_list = []
        i = 0
        while True:
            v = s[i % len(s)] + (12 * int(i/len(s))) - 1
            mc = key_mc + v
            if mc >= midi_codes.max_midi_value:
                break
            mc_list.append(mc)
            i += 1
        return mc_list, s


def unittest():
    ms = MusicScales()
    mc_list = ms.generate_midi_scale_codes("Major Scale", "C")
    for midi_code in mc_list:
        print(midi_codes.name(midi_code))


if __name__ == '__main__':
    unittest()
