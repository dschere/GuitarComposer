#!/usr/bin/env python

from view.events import Signals
from view.mainwin.mainwin import MainWindow
from controllers.appcontroller import AppController
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from services.synth.synthservice import synthservice
import sys
import atexit
import logging
import os

# setup logging for application


def setup_logger():
    fmt = "%(asctime)s %(thread)d %(filename)s:%(lineno)d %(levelname)s\n`"
    fmt += "- %(message)s"
    loglevel = os.environ.get("GC_LOGLEVEL", "DEBUG")
    if not hasattr(logging, loglevel):
        print("Warning: undefined LOGLEVEL '%s' falling back to DEBUG!" % loglevel)
        loglevel = 'DEBUG'
    logging.basicConfig(stream=sys.stdout,
                        format=fmt,
                        level=getattr(logging, loglevel)
                        )


setup_logger()


# !!!!! Create services before loading any Qt libraries
# sequence is important

# launches a child process that is dedicated to managing
# the audio synthesizer.
SynthService = synthservice()
# ^^^^ -> make this globally accessible throughout application 


##################################################################


class GuitarComposer(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.synth = SynthService
        atexit.register(self.on_shutdown)
        Signals.startup.connect(self.create_controller)

    def create_controller(self):
        self.app_controller = AppController(SynthService)

    def setup(self):
        Signals.startup.emit(self)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # Set the timer to one-shot mode
        self.timer.timeout.connect(self.on_ready)
        self.timer.start(220) #<- twitch frequency

    def on_ready(self):
        # broadcast ready event
        Signals.ready.emit(self)

    def on_shutdown(self):
        Signals.shutdown.emit(self)


if __name__ == '__main__':
    # start service
    SynthService.start()

    app = GuitarComposer(sys.argv)
    window = MainWindow()
    app.setup()
    window.show()
    sys.exit(app.exec())

    # stop service
    SynthService.shutdown()
