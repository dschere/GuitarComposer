import os
import json
from typing import List
import time
import logging

from singleton_decorator import singleton
from music.constants import Dynamic
from services.synth.synthservice import synthservice
from services.synth import sequencer as SeqEvt

from models.note import Note
from models.track import Track
from models.effect import Effects
from util.midi import midi_codes

from view.dialogs.effectsControlDialog.dialog import EffectChanges
from models.measure import TabEvent

from util.gctimer import GcTimer



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

        self.timer = GcTimer() 

        # if we have to schedule a noteoff then the timer_id
        # gets saved in the event that we play a note on the same
        # string, if that is the case we call a noteoff then cancel the inflight
        # timer which would call a premature noteoff for the new 
        # note we are playing. 
        # (chan,guitar string) -> set of running timers 
        self.timer_inflight = {}

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

    def pitchwheel_event(self, n: Note, bpm = 120):
        s = self.synth.getSequencer()

        # express duration (beats) in milliseconds.
        if not n.duration:
            raise ValueError("duration must be defined.") 
        else:        
            millisecs = int((n.duration * bpm/60.0) * 1000)

        chan_mix = self.string_map[n.string] # type: ignore
        channels = [chan for (chan,_) in chan_mix]

        # create events for potentially multiple channels.
        for chan in channels:
            if n.pitch_range != n.DEFAULT_PITCH_RANGE:
                self.synth.pitch_range(chan, n.pitch_range)
            for (when_r, pitch) in n.pitch_changes:
                when = int(when_r * millisecs)
                t_evt = SeqEvt.pitch_change(when, chan, pitch) 
                s.add(t_evt)

        # schedule events.
        s.play() 
        
    def tab_event(self, te: TabEvent, bpm: int, beat_duration: float):
        """
            generate a series of notes, effects etc in response to tab
            return the floating point number of seconds for the duration
            of this event.
        """
        te_type = te.classify()
        beats = te.beats(beat_duration)
        ev_dur = beats * (60.0 / bpm)
        # in the case of a chord, all string played ar once.
        no_stroke = not te.upstroke and not te.downstroke

        if te_type == te.REST:
            n = Note()
            n.rest = True
            n.duration = ev_dur
            self.noteoff_events(n, bpm)

        elif te_type == te.NOTE or (te_type == te.CHORD and no_stroke):
            # Either a single note or in the case of a chord with no stroke
            # were we are plucking the strings usinga finger picking techinique
            for (string,fret_val) in enumerate(te.fret):
                # a new note is to be played.
                if fret_val != -1 and te.tied_notes[string] == -1:
                    n = Note()
                    n.rest = False
                    n.fret = fret_val 
                    n.string = string
                    n.midi_code = self.tuning[string] + fret_val 
                    n.pitch_changes = te.pitch_changes
                    n.velocity = te.dynamic
                    n.set_duration(te, ev_dur)  

                    # in the case of a bend of a single string
                    # or multiple strings using the 'whammy' bar.
                    if te.pitch_bend_active: 
                        n.pitch_changes = te.pitch_changes
                        n.pitch_range = te.pitch_range

                    self.note_event(n, bpm)
        
        else:
            fret_data = list(enumerate(te.fret)) 
            # we are playing a chord 
            if te.downstroke:
                fret_data.reverse()
            start_offset_inc = te.stroke_duration / len(te.fret)
            start_offset = 0
            has_stroke = te.downstroke or te.upstroke
            for (n,(string,fret_val)) in enumerate(fret_data):
                # a new note is to be played.
                if fret_val != -1 and te.tied_notes[string] == -1:
                    n = Note()
                    n.rest = False
                    n.fret = fret_val 
                    n.string = string
                    n.midi_code = self.tuning[string] + fret_val 
                    n.pitch_changes = te.pitch_changes
                    n.velocity = te.dynamic
                    # slightly decay velocity as we pick through the strings 
                    if has_stroke:
                        n.velocity -= 2 # type: ignore
                    n.set_duration(te, ev_dur)  
                    self.note_event(n, bpm, start_offset)
                    start_offset += start_offset_inc
                
        return ev_dur

    def noteoff_events(self, n: Note, bpm=120, start_offset=0.0):
        "turn off a note for specific strings or all strings"
        s = self.synth.getSequencer()
        if n.string is None:
            for s in range(len(self.tuning)):
                n.string = s 
                self.noteoff_events(n, bpm, start_offset)
            return

        chan_mix = self.string_map[n.string]
        midicode_in_use = self.string_playing[n.string]
        if midicode_in_use:       
            for (chan, _) in chan_mix:            
                self.synth.noteoff(chan, midicode_in_use)

                timer_ids = self.timer_inflight.get((chan,n.string),[])
                for timer_id in timer_ids:
                    self.timer.cancel(timer_id)


    def note_event(self, n: Note, bpm=120, start_offset=0.0):

        "play note on potentially multiple channels"
        if n.string is None:
            logging.warning(f"note_event: Unexpected guitar string was None")
            return
        
        s = self.synth.getSequencer()
        chan_mix = self.string_map[n.string] # type: ignore

        # If we are already playing a note on this string
        # then perform a noteoff.
        midicode_in_use = self.string_playing[n.string] # type: ignore
        if self.one_note_per_string and midicode_in_use:
            for (chan, velocity_mul) in chan_mix:
                self.synth.noteoff(chan, midicode_in_use)

                timer_ids = self.timer_inflight.get((chan,n.string),[])
                for timer_id in timer_ids:
                    self.timer.cancel(timer_id)


        for (chan, velocity_mul) in chan_mix:
            midicode = self.tuning[n.string] + n.fret # type: ignore
            velocity = int(n.velocity * velocity_mul)

            # set of timers associated with this channel and guitar string
            timer_ids = set()

            if velocity > 128:
                velocity = 128    
            if n.rest:
                self.synth.noteoff(chan, midicode)                        
            else:
                if start_offset == 0.0:
                    self.synth.noteon(chan, midicode, velocity)
                else:
                    when = (start_offset * bpm/60.0)
                    timer_id = self.timer.start( when, \
                        self.synth.noteon, (chan, midicode,velocity))
                    timer_ids.add(timer_id)

                self.string_playing[n.string] = midicode # type: ignore


            # is there a pitch bend?
            if len(n.pitch_changes) > 0:
                self.synth.pitch_range(chan, n.pitch_range)
                
                for (b_when, semitones) in n.pitch_changes:
                    #millisecs = int((b_when * bpm/60.0) * 1000)
                    #t_evt = SeqEvt.pitch_change(millisecs, chan, semitones)
                    #s.add(t_evt)
                    when = (b_when * bpm/60.0)
                    timer_id = self.timer.start(when, \
                        self.synth.pitch_change, (chan,semitones))
                    timer_ids.add(timer_id)

            if n.duration is not None and n.duration > 0:
                # schedule a noteoff event in the future
                when = ((n.duration-start_offset) * bpm/60.0)
                timer_id = self.timer.start(when,
                    self.synth.noteoff, (chan, midicode))
                timer_ids.add(timer_id)

            # save collection of timers used for audio events
            if len(timer_ids) > 0:
                self.timer_inflight[(chan,n.string)] = timer_ids    

        # play any scheduled events if they exist.  
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

if __name__ == '__main__':
    import time

    ss = synthservice()
    ss.start()
    name = "12-str.GT"
    intr = Instrument(name) 

    def note_test():
        print("note test")
        n = Note() 
        n.midi_code = 60 
        n.string = 1
        n.fret = 0
        n.velocity = 100 
        n.duration = 4.0
        n.pitch_changes = [(0.1,0.25), (0.2,0.5), (0.3,1.0)]

        intr.note_event(n)
        intr.pitchwheel_event(n)

        time.sleep(5)

    def tabevent_test():
        print("tabevent test")
        te = TabEvent(6) 
        bpm = 120 
        te.downstroke = False 
        te.upstroke = True
        te.stroke_duration = 1.0
        # d major triad 
        te.fret[0] = 2
        te.fret[1] = 3
        te.fret[2] = 2
        te.fret[3] = -1
        te.fret[4] = -1
        te.fret[5] = -1

        print(te.duration)
        dur = intr.tab_event(te, bpm, 1.0) 
        print(dur)
        time.sleep(5)


    #note_test()     
    tabevent_test()
        