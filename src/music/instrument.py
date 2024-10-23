import os
import json

from singleton_decorator import singleton
from services.synth.synthservice import synthservice
from services.synth import sequencer as SeqEvt
from view.events import Signals

from models.note import Note
from util.midi import midi_codes


@singleton
class CustomInstruments:
    def __init__(self):
        filename = os.environ['GC_DATA_DIR'] + \
            "/instruments/customInstruments.json"
        self.db = json.loads(open(filename).read())

    def getSpec(self, name):
        return self.db.get(name)


StandardTuning = [
    "E4",
    "B3",
    "G3",
    "D3",
    "A2",
    "E2"
]

DropDTuning = [
    "E4",
    "B3",
    "G3",
    "D3",
    "A2",
    "D2"
]

DADGADTuning = [
    "D4",
    "A3",
    "G3",
    "D3",
    "A2",
    "D2"
]


class InstrumentInterface:
    def note_event(self, n: Note):
        "play either a note or a rest"


class MultiInstrumentImp(InstrumentInterface):
    def __init__(self, instr, multi_instr_spec):
        self.instr = instr

        # collect all the unique instrument names first
        instrument_names = set()
        string_map = multi_instr_spec.get('string_map')
        for m in string_map:
            for name in m:
                instrument_names.add(name)

        # assign midi channels for each instrument
        instr_2_chan = {}
        for name in instrument_names:
            # reserve a channel for this instrument
            instr_2_chan[name] = self.instr.synth.alloc(name)

        # create a table that maps each guitar string to a set
        # channels and velocity multipliers so that multiple
        # instruments can be used to implement a single string
        self.string_map = []
        for m in string_map:
            chan_mix = []
            for (name, velocity_mul) in m.items():
                item = (instr_2_chan[name], velocity_mul,)
                chan_mix.append(item)
            self.string_map.append(chan_mix)

        self.instr_2_chan = instr_2_chan

    def note_event(self, n: Note):
        "play note on potentially multiple channels"
        chan_mix = self.string_map[n.string]

        midicode_in_use = self.instr.string_playing[n.string]
        if self.instr.one_note_per_string and midicode_in_use:
            for (chan, velocity_mul) in chan_mix:
                self.instr.synth.noteoff(chan, midicode_in_use)

        for (chan, velocity_mul) in chan_mix:
            midicode = self.instr.tuning[n.string] + n.fret
            velocity = int(n.velocity * velocity_mul)
            if velocity > 128:
                velocity = 128
            if n.rest:
                self.instr.synth.noteoff(chan, midicode)
            else:
                self.instr.synth.noteon(chan, midicode, velocity)
                self.instr.string_playing[n.string] = midicode

            if n.duration and n.duration > 0:
                # schedule a noteoff event.
                s = self.instr.synth.getSequencer()
                # schedule a noteoff event in the future
                t_evt = SeqEvt.noteoff(n.duration, chan, midicode)
                s.add(t_evt)
                s.play()


class SingleInstrumentImp(InstrumentInterface):
    def __init__(self, instr, chan):
        self.instr = instr
        self.chan = chan

    def note_event(self, n: Note):

        midicode_in_use = self.instr.string_playing[n.string]
        if self.instr.one_note_per_string and midicode_in_use:
            self.instr.synth.noteoff(self.chan, midicode_in_use)

        midicode = self.instr.tuning[n.string] + n.fret
        velocity = int(n.velocity)

        if n.rest:
            self.instr.synth.noteoff(self.chan, midicode)
        else:
            self.instr.synth.noteon(self.chan, midicode, velocity)
            self.instr.string_playing[n.string] = midicode

        if n.duration and n.duration > 0:
            # schedule a noteoff event.
            s = self.instr.synth.getSequencer()
            # schedule a noteoff event in the future
            t_evt = SeqEvt.noteoff(n.duration, self.chan, midicode)
            s.add(t_evt)
            s.play()




class Instrument:
    """ 
    Object used to represent a midi instrument. It may also represent a collection
    of midi instruments. It acts as a conduit for communications with the synthservice
    singleton object. 

    Each instrument can be represented by multiple configured midid channels. For instance
    an electrict guitar would have a muted channel, a distortion channel, a fret
    noise channel etc.
    """

    # get references to singletons
    custom_instruments = CustomInstruments()
    synth = synthservice()

    def __init__(self, name, tuning=StandardTuning):
        self.string_playing = [None] * len(tuning)
        self.name = name
        self.tuning = [midi_codes.midi_code(name) for name in tuning]

        multi_instr_spec = self.custom_instruments.getSpec(name)
        if multi_instr_spec:
            self.implementation = MultiInstrumentImp(self, multi_instr_spec)
        else:
            chan = self.synth.alloc(name)
            if chan:
                self.implementation = SingleInstrumentImp(self, chan)
            else:
                raise ValueError(
                    "Unknown instrument name '%s' or out of channels" % name)

        # infer whether or not this instrument is a guitar or bass
        # meaning we can only play one note per string, and new not results in
        # a noteoff event
        # sadly we have to do sluthing rather than something concrete.
        self.one_note_per_string = False
        nlist = ["Guitar", "Bass", "Gtr", "GT", "Bs"]  # Bass or guitar
        exclude = ["Bassoon"]
        for n in nlist:
            if name.find(n) != -1 and n not in exclude:
                self.one_note_per_string = True
                break

    def __getattr__(self, n):
        return getattr(self.implementation, n)


def getInstrumentList():
    #Note: these are both singletons 
    custom_instruments = CustomInstruments()
    synth = synthservice()
    
    names = custom_instruments.db.keys() + \
        [spec.name for spec in synth.instrument_info()]
    names.sort()
    return names 