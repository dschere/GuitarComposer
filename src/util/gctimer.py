"""
threading.Timer is more accurate that QTimer
"""
import atexit
import threading
from typing import Tuple
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt

from singleton_decorator import singleton


@singleton
class GcTimer(QObject):
    expired = pyqtSignal(int)
    timers = {}
    id_counter = 0

    def invoke(self, timer_id):
        if timer_id in self.timers:
            (callback, args, t) = self.timers[timer_id]
            if timer_id in self.timers:
                del self.timers[timer_id]
            # invoke callback
            callback( *args )

    def _on_shutdown(self):
        for (callback, args, t) in self.timers.values():
            t.cancel()
        self.timers = {}

    def __init__(self):
        super().__init__()

        atexit.register(self._on_shutdown)

    def start(self, when : float, callback, args = ()):
        timer_id = self.id_counter 
        self.id_counter += 1

        t = threading.Timer(when, self.invoke, (timer_id,))

        self.timers[timer_id] = (callback, args, t)

        t.start()
        return timer_id

    def cancel(self, timer_id):
        if timer_id in self.timers:
            (callback, args, t) = self.timers[timer_id]
            t.cancel()
            del self.timers[timer_id]


if __name__ == '__main__':
    import sys 
    import time
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWidgets import QPushButton

    def cancel_test():
        class callback_cancel_test:
            def __init__(self, interval):
                t = GcTimer()
                self.start = time.perf_counter()
                self.timer_id = t.start(interval, self, (interval,))

            def __call__(self, interval):
                now = time.perf_counter()
                actual = now - self.start
                diff = interval - actual 
                print(f"timer {self.timer_id} diff={diff} interval={interval}")

        def cb():
            raise RuntimeError("should not have been called")

        t = GcTimer()
        tid = t.start(2.0, cb, ())
        time.sleep(0.01)
        t.cancel(tid)
        time.sleep(2.0)
        print("should be empty")
        t.stat() 

    def stress_test():

        class callback_latency_test:
            def __init__(self, interval):
                t = GcTimer()
                self.start = time.perf_counter()
                self.timer_id = t.start(interval, self, (interval,))

            def __call__(self, interval):
                now = time.perf_counter()
                actual = now - self.start
                diff = interval - actual 
                print(f"timer {self.timer_id} diff={diff} interval={interval}")

        for i in range(512):
            callback_latency_test(0.005 + ((i % 25) * 0.001))

        #GcTimer().stat()     
        

    app = QApplication(sys.argv)
    w = QPushButton("test")
    w.clicked.connect(stress_test)
    #w.clicked.connect(cancel_test)
    w.show()

    # what is the overhead of thread events ?

    # create singleton
    t = GcTimer()

    #w.clicked.connect(test_accuracy)

    sys.exit(app.exec())




