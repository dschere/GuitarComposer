import re

MidiNamePattern = re.compile("([A-G][#b]*)([0-9])")      


def midiNoteNumber(name):
    offset = 12
    result = -1
    letter_tab = {        
        'C' : 0,
        'Db': 1,
        'C#': 1,
        'D' : 2,
        'D#': 3,
        'Eb': 3,
        'E' : 4,
        'F' : 5,
        'Gb': 6,
        'F#': 6,
        'G' : 7,
        'Ab': 8,
        'G#': 8,
        'A' : 9,
        'Bb': 10,
        'A#': 10,
        'B' : 11
    }
    m = MidiNamePattern.match(name)
    if m:
        code = letter_tab.get(m.group(1))
        if not code:
            print("Invalid note name %s" % m.group(1))
        octave = int(m.group(2))
        if octave < 1:
            print("Invalid octave number %d" % octave)
        result = offset + code + (12 * octave)
    return result


def unittest():
    assert midiNoteNumber("D4") == 62
    assert midiNoteNumber("Ab3") == 56


if __name__ == '__main__':
    unittest()
