# demo code used for reference.

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import pickle
import time
from singleton_decorator import singleton


#FUTURE
def SaveSong(filename):
    """ 
    If thread running mutex set ...
        show dialog saying save in progress can't perform
    else
        start background thread to call pickle
        show popup showing time clock 
        shutdown down popup when complete
    """


"""
use mutex to prevent multiple instances of pickle worker
the dialog that kicks off this thread can close while in 
flight.
"""
class PickleWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, obj, filename):
        super().__init__()
        self.obj = obj
        self.filename = filename

    def run(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.obj, f)
        self.finished.emit()


"""
singleton 
   use a mutex to prevent multiple instances of PickleWorker
   launch pickel worker as a deamon thread.

"""
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pickle with Elapsed Time")
        self.setGeometry(100, 100, 300, 150)

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Click to save large object")
        self.time_label = QLabel("Elapsed Time: 0s")
        self.button = QPushButton("Start Saving")
        self.button.clicked.connect(self.start_saving)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.button)

        self.start_time = 0
        self.timer = QTimer()
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self.update_elapsed_time)

    def start_saving(self):
        self.label.setText("Saving...")
        self.button.setEnabled(False)
        self.start_time = time.time()
        self.timer.start()

        large_obj = list(range(10_000_000))  # Simulate a big object
        self.worker = PickleWorker(large_obj, "data.pkl")
        self.worker.finished.connect(self.done)
        self.worker.start()

    def update_elapsed_time(self):
        elapsed = int(time.time() - self.start_time)
        self.time_label.setText(f"Elapsed Time: {elapsed}s")

    def done(self):
        self.timer.stop()
        self.label.setText("Done saving!")
        self.button.setEnabled(True)


app = QApplication([])
window = MyWindow()
window.show()
app.exec()
