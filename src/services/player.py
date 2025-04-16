""" 
Interactive player. 

Processes track(s) and allows user to rewind pause skip etc.

"""

from typing import List, Tuple
from models.measure import TabEvent
from models.song import Song
from models.track import Track
from PyQt6.QtCore import QObject, QTimer, QThread, pyqtSignal
import copy
import time
from music.instrument import Instrument
from threading import Event as thread_event
from threading import Lock
from threading import Timer

from services.synth.synthservice import synthservice
from view.events import Signals, PlayerVisualEvent






class track_player_api(QObject):
    """ 
    internal api for player thead
    """
    def __init__(self, track: Track, start_measure: int, is_playing: thread_event):
        super().__init__() 

        self.intrument = Instrument(track.instrument_name)
        self.track = copy.deepcopy(track) 
        self.midx = start_measure # measure index
        self.expected_tm = None
        self.timer = None          
        self.track.set_moment(start_measure, 0)
        self.is_playing = is_playing
        self.timer_loop_lock = Lock()
        
    def stop(self):
        self.timer_loop_lock.acquire() 
        if self.timer: #<<< shared resource 
            self.timer.cancel() 
            self.timer = None
        self.timer_loop_lock.release() 

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
        evt = PlayerVisualEvent(self.track, measure) 
        Signals.player_visual_event.emit(evt)

        beat_duration = ts.beat_duration()
        duration = self.intrument.tab_event(tab_event, bpm, beat_duration)
        r = self.track.next_moment()

        return (duration,type(r) != type(None))
    
    def skip_measure(self):
        self.timer_loop_lock.acquire() 
        if self.timer: #<<< shared resource 
            self.timer.cancel()
        self.track.skip_measure() 
        self.timer_loop_lock.release() 
    
    def previous_measure(self):
        self.timer_loop_lock.acquire() 
        if self.timer: #<<< shared resource 
            self.timer.cancel()
        self.track.previous_measure()
        self.timer_loop_lock.release() 
   
    def timer_loop(self):      
        print("timer_loop called")  
        self.timer_loop_lock.acquire() 
        print("aquired lock")

        # remove old timer 
        if self.timer: 
            self.timer.cancel()
            self.timer = None 

        # if we are still playing
        if self.is_playing.is_set():
            drift = 0.0
            if self.expected_tm: 
                drift = time.time() - self.expected_tm 

            # play all note(s) in this moment in the measure, return
            # the number of milliseconds till for the next moment.
            duration_secs, more_moments = self._play_current_moment()
            print("play moment duration_secs=%f more_moments=%s drift=%f" % (
                duration_secs, str(more_moments), drift
            ))

            if more_moments:
                # compensate for clock drift of previous onshot timer plus
                # processing.
                duration_secs -= drift

                self.expected_tm = time.time() + duration_secs 
                
                # recursively call this loop function in the future.
                self.timer = Timer(duration_secs, self.timer_loop)
                self.timer.start()
        
        self.timer_loop_lock.release() 


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
            p.stop()
            p.expected_tm = None

    def resume(self):
        for p in self.track_players:

            p.timer_loop()


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
        # if x == 1:
        #     te.upstroke = True 
        # elif x == 0:
        #     te.downstroke = True 
        for (string,fret) in chord:
            te.fret[string] = fret
        te.duration = 2.0    

    i = 0
    te, me = t.current_moment()
    setup_momement([(5,0)], te, 0)
    for i in range(12):
        r = t.next_moment() 
        if not r:
            break
        te, me = t.current_moment()
        setup_momement([(5,i+1)], te, i % 2)
       
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



if __name__ == '__main__':
    unittest()

