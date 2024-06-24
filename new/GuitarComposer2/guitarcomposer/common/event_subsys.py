"""
pub/sub event system that allows for controllers to be decoupled
from UI code. 
"""
import traceback
import atexit

from threading import Event as thread_event
from singleton_decorator import singleton
from subpub import SubPub, Msg

from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSlot


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, q, fn, workers):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.finished = thread_event()
        self.q = q
        self.workers = workers

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        while not self.finished.is_set():
            match, data = self.q.get()
            if not match:
                self.finished.set()
                return
                
            self.fn(match, data, self.finished)
                     
        self.workers.remove(self)  
        self.finished.set()


@singleton
class event_subsys:
    def __init__(self):
        self.sp = SubPub()
        self.threadpool = QThreadPool()
        self.workers = set()

        atexit.register( self.cleanup )

    def subscribe(self, topic, callback):
        """ Launch a deadicated worker thread to handle topics.
            The topic can be a string or regular expression. 
        """
        q = self.sp.subscribe(topic)
        worker = Worker(q, callback, self.workers)
        self.workers.add(worker)
        self.threadpool.start(worker)
        return worker
        
    def unsubscribe(self, worker):
        "retire worker"
        worker.q.put(Msg(None, None))
        worker.finished.wait()
        self.workers.remove(worker)
        
    def publish(self, topic, data):
        "publish data to a topic"
        return self.sp.publish(topic, data)    
            
    def cleanup(self):
        "retire all workers"
        self.threadpool.clear()
        while len(self.workers) > 0:
            worker = self.workers.pop()
            worker.q.put(Msg(None, None))
            worker.finished.wait()
        self.workers = set()
        
# ---- topics --------------------------------        
        
# main menu bar topics.
MAIN_MENU_NEW = "main_menu/File/New"
MAIN_MENU_OPEN = "main_menu/File/Open"
MAIN_MENU_EXIT = "main_menu/File/Exit"
MAIN_MENU_UNDO = "main_menu/Edit/Undo"
MAIN_MENU_REDO = "main_menu/Edit/Redo"
MAIN_MENU_COPY = "main_menu/Edit/Copy"
MAIN_MENU_PASTE = "main_menu/Edit/Paste"

# song tab selected
SONG_TAB_SELECTED = "songtabselect"

# keyboard events
KEY_PRESS = "keypress"
KEY_RELEASE = "keyrelease" 

# note dynamic select
DYNAMIC_SELECTED = "dynamic_selected"
NOTE_SELECTED = "note_selected"


    
# unit test code
if __name__ == '__main__':
    import sys, time
    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)
    EventSubSys = event_subsys()
    
    def handler(match, data, finished):
        print((match.string,data))
        #finished.set()

    w = EventSubSys.subscribe("bar2", lambda match,data,finished: finished.set())        
    EventSubSys.subscribe("bar", lambda match,data,finished: finished.set())        
    EventSubSys.subscribe("foo", handler)
    time.sleep(1)
    EventSubSys.publish("foo", "this is a test")
    EventSubSys.publish("bar", "another test")
    time.sleep(1)
    assert len(EventSubSys.workers) ==  2
    EventSubSys.unsubscribe(w)
    assert len(EventSubSys.workers) ==  1
    
    EventSubSys.cleanup()
    assert len(EventSubSys.workers) ==  0
    
    window = QMainWindow()
    window.show()
    sys.exit(app.exec())
      

# One and only global instance.
EventSubSys = event_subsys()

