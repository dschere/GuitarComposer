import os
import json

from singleton_decorator import singleton
from services.synth.synthservice import synthservice
from services.synth import sequencer as SeqEvt

from models.note import Note
from models.track import Track
from models.effect import Effects
from util.midi import midi_codes

from view.widgets.effectsControlDialog.effectsControls import EffectChanges

@singleton
class CustomInstruments:
    def __init__(self):
        filename = os.environ['GC_DATA_DIR'] + \
            "/instruments/customInstruments.json"
        self.db = json.loads(open(filename).read())

    def getSpec(self, name):
        return self.db.get(name)


StandardTuning = Track().tuning

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


class InstrumentBaseImp:
    def __init__(self):
        self.effect_enabled_state = set()

    def note_event(self, n: Note):
        "play either a note or a rest"    

    def update_effect_changes(self, synth, chan, ec: EffectChanges ):
        # see EffectsDialog.delta for details on EffectChanges
        for e in ec:
            path = e.plugin_path() 
            label = e.plugin_label() 

            if e.is_enabled():
                if chan not in self.effect_enabled_state:
                    print(f"add filter {label}")
                    synth.filter_add(chan, path, label)
                    print(f"enable filter {label}")
                    synth.filter_enable(chan, label)
                    self.effect_enabled_state.add(chan)

                # change/set parameters
                for (pname,param) in ec[e]:
                    print(f"set {pname} to {param.current_value}")
                    synth.filter_set_control_by_name(
                        chan,
                        label,
                        pname,
                        param.current_value
                    )
                    
            elif chan in self.effect_enabled_state:
                synth.filter_disable(chan, label)
                synth.filter_remove(chan, label)
                self.effect_enabled_state.remove(chan)
            

class MultiInstrumentImp(InstrumentBaseImp):
    def __init__(self, instr, multi_instr_spec):
        super().__init__()
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
        self.channels_used = set(instr_2_chan.values())

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

    def free_resources(self):
        for chan in self.channels_used:
            self.instr.synth.dealloc(chan)

    def effects_change(self, ec: EffectChanges):
        for chan in self.channels_used:
            self.update_effect_changes(self.instr.synth, chan, ec)

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


class SingleInstrumentImp(InstrumentBaseImp):
    def __init__(self, instr, chan):
        super().__init__()
        self.instr = instr
        self.chan = chan

    def free_resources(self):
        self.instr.synth.dealloc(self.chan)

    def effects_change(self, ec: EffectChanges):
        self.update_effect_changes(self.instr.synth, self.chan, ec)

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
    Object used to represent a midi instrument. It may also
    represent a collection of midi instruments. It acts as a
    conduit for communications with the synthservice
    singleton object.

    Each instrument can be represented by multiple configured
    midi channels. For instance an electrict guitar would have
    a muted channel, a distortion channel, a fret noise channel etc.
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
    # Note: these are both singletons
    custom_instruments = CustomInstruments()
    synth = synthservice()

    names = list(custom_instruments.db.keys())
    for sf_spec in synth.instrument_info():
        for instr_spec in sf_spec['instruments']:
            names.append(instr_spec['name'])
    names.sort()
    return names
