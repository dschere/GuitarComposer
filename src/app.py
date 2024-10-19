#!/usr/bin/env python

import sys
import atexit
import logging
import os

# setup logging for application
def setup_logger():
    fmt = "%(asctime)s %(thread)d %(filename)s:%(lineno)d %(levelname)s\n`"
    fmt += "- %(message)s"
    loglevel = os.environ.get("GC_LOGLEVEL","DEBUG")
    if not hasattr(logging,loglevel):
        print("Warning: undefined LOGLEVEL '%s' falling back to DEBUG!" % loglevel)
        loglevel = 'DEBUG'      
    logging.basicConfig(stream=sys.stdout,
        format=fmt,
        level=getattr(logging,loglevel)
    )
setup_logger()


# !!!!! Create services before loading any Qt libraries
# sequence is important 
from services.synth.synthservice import synthservice

# launches a child process that is dedicated to managing
# the audio synthesizer.
SynthService = synthservice()


##################################################################

from PyQt6.QtWidgets import QApplication

from controllers.appcontroller import AppController
from view.mainwin.mainwin import MainWindow
from view.events import Signals

class GuitarComposer(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        atexit.register(self.on_shutdown)
        Signals.startup.connect(self.create_controller)

    def create_controller(self):
        self.app_controller = AppController(SynthService)            

    def setup(self):
        Signals.startup.emit(self)

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

