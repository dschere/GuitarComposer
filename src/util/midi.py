"""
This module allows for midi codes to be identified with a note name
such as A#4 -> A# forth octave -> midi code and visa versa.
"""
from singleton_decorator import singleton
import re


FLAT_SIGN = "\u266d"
SHARP_SIGN = "\u266f"


@singleton
class _midi_codes:
    re_key_and_octave = re.compile('([A-G#b]+)([0-9]+)')
    re_key_only = re.compile('([A-G#b]+)')
    min_midi_value = 24
    max_midi_value = 128

    # setup static looup tables
    # Here is a reference https://computermusicresource.com/midikeys.html
    SHARP_INDEX = 0
    FLAT_INDEX = 1
    name_to_code = {}
    code_to_name = {}
    all_names = []

    accent_to_index = {
        '#': SHARP_INDEX,
        'b': FLAT_INDEX
    }

    names = [
        ('C', 'C'),
        ('C#', 'Db'),
        ('D', 'D'),
        ('D#', 'Eb'),
        ('E', 'E'),
        ('F', 'F'),
        ('F#', 'Gb'),
        ('G', 'G'),
        ('G#', 'Ab'),
        ('A', 'A'),
        ('A#', 'Bb'),
        ('B', 'B')]

    for midi_code in range(min_midi_value, max_midi_value):
        octave = int((midi_code - 24) / 12)
        s_name = names[midi_code % 12][SHARP_INDEX] + str(octave)
        b_name = names[midi_code % 12][FLAT_INDEX] + str(octave)

        if s_name == b_name:
            all_names.append(s_name)
        else:
            n = s_name+"/"+b_name
            all_names.append(n)
            name_to_code[n] = midi_code

        name_to_code[s_name] = midi_code
        name_to_code[b_name] = midi_code

        code_to_name[midi_code] = (s_name, b_name)

    def name(self, midi_code, accent='#'):
        i = self.accent_to_index[accent]
        return self.code_to_name[midi_code][i]

    def midi_code(self, name):
        if self.re_key_and_octave.match(name):
            return self.name_to_code[name]
        elif self.re_key_only.match(name):
            name += "3"
            return self.name_to_code[name]

    def generic_names(self):
        return self.all_names

    def get_staff_accents(self, key_name):
        a_map = {
            '#': SHARP_SIGN,
            'b': FLAT_SIGN
        }
        steps = [2, 2, 1, 2, 2, 2, 1]  # major scale
        self.key_name = key_name
        key_notes = []

        accent = '#'
        if key_name in ("F", "Bb", "Eb", "Ab"):
            accent = "b"

        name = key_name + "5"
        midi = self.midi_code(name)

        for step in steps:
            print((name, midi))
            if accent in name:
                key_notes.append((a_map[accent], midi))
            midi += step
            if midi > 92:
                midi -= 12
            name = self.name(midi, accent)

        return key_notes


midi_codes = _midi_codes()
