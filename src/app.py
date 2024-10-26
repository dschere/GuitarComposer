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

        # setup controllers first
        self.app_controller = AppController(SynthService)
        atexit.register(self.on_shutdown)


    def on_shutdown(self):
        Signals.shutdown.emit(self)


def main():
    logging.debug("Running with debug log level")
    # start service
    SynthService.start()

    app = GuitarComposer(sys.argv)
    window = MainWindow()
    window.show()
    
    # broadcast ready event
    #   synth started
    #   controllers loaded
    #   gui created
    Signals.ready.emit(app)

    sys.exit(app.exec()) #<- main event loop

    # stop service
    SynthService.shutdown()

def lint_project():
    from pylint import run_pylint
    import glob
    
    base_dir = os.environ['GC_CODE_DIR']
    cmd = "find %s -name \"*.py\""
    flist = [f[:-1] for f in os.popen(cmd % base_dir).readlines()]
    sys.argv = [sys.argv[0],'--errors-only'] + flist
    run_pylint()



if __name__ == '__main__':
    cmd = "exec"
    if len(sys.argv) == 2:
        cmd = sys.argv[1]

    if cmd == "lint":    
        lint_project()
    else:    
        main()