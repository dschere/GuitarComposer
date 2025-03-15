import os
import json

from singleton_decorator import singleton
from services.synth.synthservice import synthservice
from services.synth import sequencer as SeqEvt

from models.note import Note
from models.track import Track
from models.effect import Effects
from util.midi import midi_codes

from view.dialogs.effectsControlDialog.effectsControls import EffectChanges

@singleton
class CustomInstruments:
    def __init__(self):
        filename = os.environ['GC_DATA_DIR'] + \
            "/instruments/customInstruments.json"
        self.db = json.loads(open(filename).read())

    def getSpec(self, name):
        return self.db.get(name, {
            "string_map": [
                {name: 1.0},
                {name: 1.0},
                {name: 1.0},
                {name: 1.0},
                {name: 1.0},
                {name: 1.0}
            ]
        })


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


class Instrument:
    # get references to singletons
    custom_instruments = CustomInstruments()
    synth = synthservice()


    def __init__(self, name, tuning=StandardTuning):
        self.string_playing = [None] * len(tuning)
        self.name = name
        self.tuning = [midi_codes.midi_code(name) for name in tuning]
        self.effect_enabled_state = set()

        multi_instr_spec = self.custom_instruments.getSpec(name)

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
            instr_2_chan[name] = self.synth.alloc(name)
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
        
    def update_effect_changes(self, synth, chan, ec: EffectChanges ):
        # see EffectsDialog.delta for details on EffectChanges
        for e in ec:
            path = e.plugin_path() 
            label = e.plugin_label() 

            if e.is_enabled():
                if chan not in self.effect_enabled_state:
                    synth.filter_add(chan, path, label)
                    synth.filter_enable(chan, label)
                    self.effect_enabled_state.add(chan)

                # change/set parameters
                for (pname,param) in ec[e]:
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

    
    def free_resources(self):
        for chan in self.channels_used:
            self.synth.dealloc(chan)

    def effects_change(self, ec: EffectChanges):
        for chan in self.channels_used:
            self.update_effect_changes(self.synth, chan, ec)

    def note_event(self, n: Note):
        "play note on potentially multiple channels"
        chan_mix = self.string_map[n.string] # type: ignore

        midicode_in_use = self.string_playing[n.string] # type: ignore
        if self.one_note_per_string and midicode_in_use:
            for (chan, velocity_mul) in chan_mix:
                self.synth.noteoff(chan, midicode_in_use)

        for (chan, velocity_mul) in chan_mix:
            midicode = self.tuning[n.string] + n.fret # type: ignore
            velocity = int(n.velocity * velocity_mul)
            if velocity > 128:
                velocity = 128
            if n.rest:
                self.synth.noteoff(chan, midicode)
            else:
                self.synth.noteon(chan, midicode, velocity)
                self.string_playing[n.string] = midicode # type: ignore

            if n.duration and n.duration > 0:
                # schedule a noteoff event.
                s = self.synth.getSequencer()
                # schedule a noteoff event in the future
                t_evt = SeqEvt.noteoff(n.duration, chan, midicode)
                s.add(t_evt)
                s.play()



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
