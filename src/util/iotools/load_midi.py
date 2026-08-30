"""
Load midi file as a Song object.
"""
import partitura 
from partitura import score
from partitura.score import Note, Rest, fill_rests

from models.measure import Measure, TabEvent, TimeSig, TUPLET_DISABLED
from models.song import Song
from models.track import Track
from models.note import Note as GC_Note 


from services.synth.synthservice import synthservice
from music import durationtypes as dt
from util.midi import midi_codes

from view.events import Signals, ProgressEvent
import logging

def _send_event(severity, msg, value=-1.0):
    evt = ProgressEvent("load_midi", severity, msg, value)
    Signals.progress_event.emit(evt)


def _arrange(track: Track, m: Measure):
    
    # find an optimal fret position
    # starting midi code per string 
    midi_tuning = [midi_codes.midi_code(sym) for sym in track.tuning]

    #TODO, create a sane arrangement, not this quick and dirty hack.
    for te in m.tab_events:
        if len(te.midi_codes) > 0:
            te.midi_codes.sort(reverse=True) 
            for midi_code in te.midi_codes[:len(midi_tuning)]:
                for gstring in range(0,len(midi_tuning)):
                    if te.fret[gstring] == -1:
                        fret = midi_code - midi_tuning[gstring]
                        if fret < 0:
                            continue
                        te.fret[gstring] = fret

def _approximate_note_rhythm(duration_in_beats) -> dict:
    """
    Approximates the note type, dot count, and tuplet ratio 
    given a duration in quarter-note beats.
    """
    # 1. Map base note types to their exact quarter-note beat values
    base_notes = {
        "whole": 4.0,
        "half": 2.0,
        "quarter": 1.0,
        "eighth": 0.5,
        "16th": 0.25,
        "32nd": 0.125,
        "64th": 0.0625
    }
    
    # 2. Define dot modifiers (multiplier coefficients)
    # 0 dots = 1.0, 1 dot = 1.5, 2 dots = 1.75
    dot_modifiers = [
        {"dots": 0, "multiplier": 1.0},
        {"dots": 1, "multiplier": 1.5},
        {"dots": 2, "multiplier": 1.75}
    ]
    
    # 3. Define common tuplet ratios (actual_notes_played : normal_note_space)
    # e.g., 3 notes in the space of 2 (triplet) scales duration by 2/3
    tuplet_ratios = [
        {"label": None, "multiplier": 1.0},
        {"label": "3:2", "multiplier": 2 / 3},   # Triplet
        {"label": "5:4", "multiplier": 4 / 5},   # Quintuplet
        {"label": "7:4", "multiplier": 4 / 7}    # Septuplet
    ]
    
    best_match = None
    min_error = float("inf")
    
    # 4. Search the combination grid
    for name, base_val in base_notes.items():
        for dot in dot_modifiers:
            for tuplet in tuplet_ratios:
                
                # Calculate what this exact rhythmic combination should weigh in beats
                target_duration = base_val * dot["multiplier"] * tuplet["multiplier"]
                
                # Measure absolute distance from the input duration
                error = abs(duration_in_beats - target_duration)
                
                # Keep the candidate with the lowest error
                if error < min_error:
                    min_error = error
                    best_match = {
                        "type": name,
                        "dots": dot["dots"],
                        "tuplet": tuplet["label"],
                        "expected_beats": round(target_duration, 4),
                        "error": round(error, 6)
                    }
    if best_match is None:
        return {}
    return best_match

def _compute_duration(element, beats) -> TabEvent:
    te = TabEvent(6)
    sd = element.symbolic_duration

    if sd.get('type') is None:
        sd = _approximate_note_rhythm(beats)
    dots = sd.get('dots',0)

    te.duration = {
        'whole': dt.WHOLE,
        'half': dt.HALF,
        'quarter': dt.QUARTER,
        'eighth': dt.EIGHTH,
        '16th': dt.SIXTEENTH,
        '32nd': dt.THIRTYSECOND,
        '64th': dt.SIXTYFORTH,
        '128th': dt.SIXTYFORTH / 2,
        '256th': dt.SIXTYFORTH / 4,
        None: None
    }[sd.get('type')]
    if dots == 1:
        te.dotted = True 
    elif dots == 2:
        te.double_dotted = True    
    te.tuplet_code = sd.get('actual_notes',TUPLET_DISABLED)    
    return te

def _append_tab_event(m: Measure, ts: TimeSig, element_group, beats):
    n=GC_Note()
    n.duration = beats
    te = _compute_duration(element_group[0], beats)

    if isinstance(element_group[0], Note):                    
        te.midi_codes = [int(e.midi_pitch) for e in element_group] # type: ignore
        te.dynamic = getattr(element_group[0],"velocity") if hasattr(element_group[0],"velocity") else 64

    elif isinstance(element_group[0], Rest):
        te.midi_codes = []  # type: ignore

    m.tab_events.append(te)



def _load_midi(midi_filename) -> Song:
    s = Song()
    _send_event(logging.INFO,f"Loading midi file {midi_filename}")

    ss = synthservice()
    
    performance = partitura.load_performance_midi(midi_filename)
    music_score = partitura.load_score_midi(midi_filename, ensure_list=True) # type: ignore


    tracks = []

    for part in performance.performedparts:
        if part.programs:
            t = Track()
            t.instrument_name = ss.instrument_name_by_preset(0) 
            for prog in part.programs:
                program_number = prog["program"]
                t.instrument_name = ss.instrument_name_by_preset(program_number)
            tracks.append(t)

    for (i,part) in enumerate(music_score):
        percentage_done = (100 * i/len(music_score))
        _send_event(logging.INFO,f"%{round(percentage_done,2)} done.",percentage_done)

        t = tracks[i]
        current_track : Track = t
        score.add_measures(part)

        bpm_per_measure = {}

        tempos = sorted(part.iter_all(score.Tempo), key=lambda p: p.start.t)

        for note in part.iter_all(score.GenericNote, include_subclasses=True):
            if note.voice is None:
                note.voice = 1
            if note.staff is None:
                note.staff = 1


        # Optional: force a dummy rest in completely empty measures
        for m in part.measures:
            notes = list(part.iter_all(score.GenericNote, m.start.t, m.end.t, include_subclasses=True))
            if len(notes) == 0:
                rest = score.Rest(voice=1, staff=1)
                part.add(rest, m.start.t, m.end.t)

            # Update current BPM with any tempo that starts at or before this measure
            while tempos and tempos[0].start.t <= m.start.t:
                current_bpm = tempos[0].bpm
                tempos.pop(0)
    
            bpm_per_measure[m] = int(current_bpm)


        score.fill_rests(part)


        for (mnum,measure) in enumerate(part.iter_all(score.Measure)):
            
            beats, beat_type = part.time_signature_map(measure.start.t)[:2]
            ts = TimeSig()
            ts.beats_per_measure = int(beats) # type: ignore
            ts.beat_note_id = int(beat_type) 

            bpm = bpm_per_measure[measure]

            
            elements = list(
                part.iter_all(
                    score.GenericNote,
                    include_subclasses=True,   # includes both Note and Rest
                    start=measure.start.t,
                    end=measure.end.t
                )
            )

            # group elements with the same start time (chords)
            group_elements = []
            for element in elements:
                if len(group_elements) == 0:
                    group_elements.append([element])
                elif group_elements[-1][0].start.t == element.start.t:
                    group_elements[-1].append(element)
                else:
                    group_elements.append([element])


            m = Measure(timesig=ts, bpm=bpm)
            m.cleff = current_track.cleff

            for element_group in group_elements:
                _append_tab_event(m, ts, element_group, beats)

            # provide a best effort arrangement of fingering
            _arrange(t, m)
            current_track.measures.append(m)    # type: ignore


    s.tracks = tracks    
    _send_event(logging.INFO,f"Completed loading midi file {midi_filename}")
    return s

def load_midi(midi_filename) -> Song:
    try:
        return _load_midi(midi_filename)
    except Exception as e:
        _send_event(logging.ERROR, str(e))
        raise e


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    def progress_handler(evt: ProgressEvent):
        print(f"progress_handler: {evt.sender_id} {evt.severity} {evt.msg}")
    Signals.progress_event.connect(progress_handler)    

    #load_midi("/home/david/Downloads/Rush—Xanadu.mid")
    load_midi("/home/david/Downloads/mars-bringer-f-war.mid")




















