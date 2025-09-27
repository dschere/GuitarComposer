""" 
Interactive player. 

Processes track(s) and allows user to rewind pause skip etc.

"""

from typing import List, Tuple
from models.measure import Measure, TabEvent
from models.song import Song
from models.track import Track
from PyQt6.QtCore import QObject, QTimer, QThread, pyqtSignal
import copy
import time
from music.constants import Dynamic
from music.instrument import Instrument
from threading import Event as thread_event
from threading import Lock
#from threading import Timer
from util.gctimer import GcTimer

from services.synth.synthservice import synthservice
from view.events import Signals, PlayerVisualEvent



def PlayMoment(track: Track, instrument: Instrument):
    """ 
    play a single moment of a track using using the supplied track
    """
    timer = GcTimer()

    (tab_event, measure) = track.current_moment()
    (ts, bpm, _, _) = track.getMeasureParams(measure)

    # emit signal to update visuals
    on_evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_ON, tab_event) 
    Signals.player_visual_event.emit(on_evt)

    beat_duration = ts.beat_duration()
    duration = instrument.tab_event(tab_event, bpm, beat_duration)

    class turn_off_highlight:
        def __init__(self, tab_event):
            self.tab_event = tab_event 
        def __call__(self):
            off_evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_OFF, tab_event) 
            Signals.player_visual_event.emit(off_evt)

    timer.start(duration,turn_off_highlight(tab_event))



def compile_track(track: Track, m_idx=0) -> List[Tuple[TabEvent,Measure]]:
    """ 
    Walk through track and generate a list of tab events, unravel all repeat loops
    so that we have a single vector that the player can walk through.

    Return a List of (tab_event,measure)
    """
    class repeat_item:
        def __init__(self, **kw):
            self.start_measure = kw.get('start',-1)
            self.end_measure = kw.get('end',-1)
            self.repeat_counter = kw.get('count',-1)
            self.tab_events = []

    result = []
    repeat_stack = []
    
    while m_idx < len(track.measures):
        m = track.measures[m_idx]

        if m.start_repeat:
            r = repeat_item(start=m.measure_number)
            repeat_stack = [r] + repeat_stack

        for _te in m.tab_events:
            te = copy.deepcopy(_te)
            if len(repeat_stack) == 0:
                result.append((te, m))
            else:
                r : repeat_item = repeat_stack[0]
                r.tab_events.append((te,m))        

        if m.end_repeat:
            r : repeat_item = repeat_stack[0]
            if r.end_measure == -1:
                r.end_measure = m.measure_number
                r.repeat_counter = m.repeat_count
            
            tab_events = r.tab_events * (r.repeat_counter + 1) 
            del repeat_stack[0]
            if len(repeat_stack) > 0:
                repeat_stack[0].tab_events += tab_events
            else:
                result += tab_events
            
        m_idx += 1

    # print("compiled result: ")
    # for (te,m) in result:
    #     print((te.fret, m.measure_number))
    # print("-----------------------------------------")

    # walk the track applying dynamics and articulations, when encountered they change
    # the settings for the current and all subsiquent tab events until a new one 
    # encountered.
    dynamic = Dynamic.MF
    legato = False 
    staccato = False

    for te,m in result:
        if te.dynamic is None:
            te.dynamic = dynamic
        else:
            dynamic = te.dynamic

        if te.legato is None:
            te.legato = legato 
        else:
            legato = te.legato 

        if te.staccato is None:
            te.staccato = staccato 
        else:
            staccato = te.staccato


    return result    



class track_player_api(QObject):
    """ 
    internal api for player thead
    """
    def __init__(self, track: Track, start_measure: int, is_playing: thread_event):
        super().__init__() 

        self.intrument = Instrument(track.instrument_name)
        self.track = track 
        self.midx = start_measure # measure index
        self.expected_tm = None
        self.timer_id = -1
        self.timer = GcTimer()
        self.track.set_moment(start_measure, 0)
        self.is_playing = is_playing
        self.start_measure = start_measure
        self.timer_loop_lock = Lock()

        self.linear_tabs = [] 
        self.linear_tab_idx = 0

    def _play_current_moment(self) -> Tuple[float,bool]:
        """
        play the current moment within a track, return 
        (
           the floating point timeof the next moment,
           boolean -> are there more moments to play?
        ) 

        This is called within the timer loop no external calls
        allowed.
        """
        (tab_event, measure) = self.track.current_moment()
        (ts, bpm, _, _) = self.track.getMeasureParams(measure)
 
        # emit signal to update visuals
        evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_ON, tab_event) 
        Signals.player_visual_event.emit(evt)

        beat_duration = ts.beat_duration()
        duration = self.intrument.tab_event(tab_event, bpm, beat_duration)
        r = self.track.next_moment()

        return (duration,type(r) != type(None))
        
    def skip_measure(self):
        if self.timer_id != -1:
            self.timer.cancel(self.timer_id)
        self.track.skip_measure() 
    
    def previous_measure(self):
        if self.timer_id != -1:
            self.timer.cancel(self.timer_id)
        self.track.previous_measure()
        
    def _play_loop(self, i, linear_tabs):
        self.linear_tab_idx = i
        if i < len(linear_tabs) and self.is_playing.is_set():
            (tab_event, measure) = linear_tabs[i]
            (ts, bpm, _, _) = self.track.getMeasureParams(measure)
    
            # emit signal to update visuals
            evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_ON, tab_event) 
            evt.measure = measure
            Signals.player_visual_event.emit(evt)

            if i > 0:
                (prev_tab_event, prev_measure) = linear_tabs[i-1]
                p_evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_OFF, prev_tab_event)
                p_evt.measure = prev_measure 
                Signals.player_visual_event.emit(p_evt)

            beat_duration = ts.beat_duration()
            duration = self.intrument.tab_event(tab_event, bpm, beat_duration)
            
            # call next moment 
            self.timer_id = self.timer.start(duration, 
                self._play_loop, (i+1,linear_tabs))
            
        elif i == len(linear_tabs) and len(linear_tabs) > 0:
            (prev_tab_event, prev_measure) = linear_tabs[i-1]
            p_evt = PlayerVisualEvent(PlayerVisualEvent.TABEVENT_HIGHLIGHT_OFF, prev_tab_event)
            p_evt.measure = prev_measure 
            Signals.player_visual_event.emit(p_evt)


        elif self.timer_id != -1:
            self.timer.cancel(self.timer_id)
            self.timer_id = -1

        
    def play(self):
        self.linear_tabs = compile_track(self.track)
        if len(self.linear_tabs) > 0:
            self.is_playing.set()
            self._play_loop(0, self.linear_tabs)     

    def resume(self):
        if self.linear_tab_idx < len(self.linear_tabs):
            self.is_playing.set()
            self._play_loop(self.linear_tab_idx, self.linear_tabs)
        else:
            self.play()

    #expected_tm = None

    def timer_loop(self):      
        # if we are still playing
        if self.is_playing.is_set():
            # if self.expected_tm:
            #     drift = self.expected_tm - time.perf_counter()
            #     print(f"drift = {drift}")        

            # play all note(s) in this moment in the measure, return
            # the number of milliseconds till for the next moment.
            duration_secs, more_moments = self._play_current_moment()
            if more_moments:
                #self.expected_tm = time.perf_counter() + duration_secs
                self.timer = GcTimer().start(duration_secs, self.timer_loop, ())

        
    def stop(self, reset_start_measure=True):
        if self.timer_id != -1:
            self.timer.cancel(self.timer_id)
            self.timer_id = -1
        self.intrument.stop()    

        if reset_start_measure:
            self.linear_tab_idx = 0
            self.linear_tabs = []
            self.track.set_moment(self.start_measure, 0)

        p_evt = PlayerVisualEvent(PlayerVisualEvent.CLEAR_ALL, TabEvent(6))
        Signals.player_visual_event.emit(p_evt)

    def pause(self):
        # stop but do not rewind to starting meaasure
        self.stop(False)



class Player:
    def __init__(self, tracks : List[Track], start_measure = 0):
        self.is_playing = thread_event()
        self.is_playing.clear()
        self.track_players = []
        for track in tracks:
            p = track_player_api(track, start_measure, self.is_playing) 
            self.track_players.append(p)
        
    def start(self):
        self.is_playing.set()
        for p in self.track_players:
            p.timer_loop()

    def skip_measure(self): 
        self.is_playing.clear()
        for p in self.track_players:
            p.skip_measure() 
        self.start()

    def previous_measure(self):
        self.is_playing.clear() 
        for p in self.track_players:
            p.previous_measure() 
        self.start()

    def stop(self):
        self.is_playing.clear()
        for p in self.track_players:
            p.stop()

    def pause(self):
        for p in self.track_players:
            p.pause()
            p.expected_tm = None

    def resume(self):
        for p in self.track_players:
            p.resume()

    def play(self):
        for p in self.track_players:
            p.play()


def unittest():
    import sys 
    import time
    from PyQt6.QtCore import QCoreApplication

    app = QCoreApplication(sys.argv)

    ss = synthservice()
    ss.start()


    t = Track()
    t.instrument_name = "12-str.GT"
    t.append_measure()
    t.append_measure()


    t.current_measure = 0
    t.measures[t.current_measure].current_tab_event = 0

    
    def setup_momement(chord, te : TabEvent, x):
        if x == 1:
            te.upstroke = True 
        elif x == 0:
            te.downstroke = True 
        for (string,fret) in chord:
            te.fret[string] = fret
        te.duration = 1.0 
        te.dynamic = 50  

    i = 0
    te, me = t.current_moment()
    setup_momement([(5,0)], te, 0)
    for i in range(12):
        r = t.next_moment() 
        if not r:
            break
        te, me = t.current_moment()
        setup_momement([(5,i+1),(4,i+2),(3,i+1)], te, i % 2)
       
    class runner(QThread):
        def __init__(self):
            super().__init__()
            
        def run(self):
            p = Player([t],0)
            p.start()
            time.sleep(20)
            p.stop()
            app.exit(0)

    r = runner() 
    r.start()


    sys.exit(app.exec())


def test_compile_track():
    t = Track()
    t.append_measure()
    t.append_measure()

    t.measures[0].start_repeat = True
    t.measures[0].end_repeat = False
    t.measures[0].repeat_count = -1
    t.measures[0].measure_number = 1


    t.measures[1].start_repeat = True
    t.measures[1].end_repeat = True
    t.measures[1].repeat_count = 1 
    t.measures[1].measure_number = 2

    t.measures[2].start_repeat = False
    t.measures[2].end_repeat = True
    t.measures[2].repeat_count = 1 
    t.measures[2].measure_number = 3

    compile_track(t)


if __name__ == '__main__':
    test_compile_track()
    #unittest()

