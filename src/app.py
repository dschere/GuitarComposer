#!/usr/bin/env python

from view.events import Signals
from view.mainwin.mainwin import MainWindow
from controllers.appcontroller import AppController
from controllers.editorcontroller import EditorController
from controllers.playercontroller import PlayerController
from PyQt6.QtWidgets import QApplication
from services.synth.synthservice import synthservice
import sys
import atexit
import logging
import os
import qdarktheme
import signal


# setup signal handlers to aid in troublshooting
# SIGUSR1 dumps the current call stack, SIGUSR2
# prints out stack traces for each thread.
def dump_current_call_stack(*args):
    import inspect

    stack = inspect.stack()
    for frame_info in stack:
        print(frame_info.filename, frame_info.lineno, frame_info.function)
signal.signal(signal.SIGUSR1, dump_current_call_stack)

def print_all_thread_stack_traces(*args):
    import threading
    import traceback

    for thread in threading.enumerate():
        if thread.ident:
            print(f"Thread: {thread.name} ID: {thread.ident}")
            frame = sys._current_frames().get(thread.ident)
            if frame:
                traceback.print_stack(frame)
            else:
                print("No stack trace available.")
        else:
            print("Unknown thread " + str(vars(thread)))
signal.signal(signal.SIGUSR2, print_all_thread_stack_traces)


# setup logging for application


def setup_logger():
    fmt = "%(asctime)s %(thread)d %(filename)s:%(lineno)d %(levelname)s\n`"
    fmt += "- %(message)s"
    loglevel = os.environ.get("GC_LOGLEVEL", "DEBUG")
    if not hasattr(logging, loglevel):
        f = "Warning: undefined LOGLEVEL '%s' falling back to DEBUG!"
        print(f % loglevel)
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
        self.editor_controller = EditorController()
        self.player_controller = PlayerController()

        atexit.register(self.on_shutdown)

    def on_shutdown(self):
        Signals.shutdown.emit(self)


def main():
    logging.debug("Running with debug log level")
    # start service
    SynthService.start()

    app = GuitarComposer(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    window = MainWindow(app.editor_controller)
    window.show()

    # broadcast ready event
    #   synth started
    #   controllers loaded
    #   gui created
    Signals.ready.emit(app)

    sys.exit(app.exec())  # <- main event loop
    
    # stop service
    SynthService.shutdown()


if __name__ == '__main__':
    main()
