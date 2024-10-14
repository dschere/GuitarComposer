import sys
import atexit

from PyQt6.QtWidgets import QApplication

import services
from controllers.appcontroller import AppController


class Application(QApplication):
    def __init__(self):
        self.synth_service = services.SynthService
        atexit.register(self.shutdown)

    def setup(self):
        self.synth_service.start()
        self.app_controller = AppController(self)

    def shutdown(self):
        self.synth_service.stop()


if __name__ == '__main__':
    app = Application()
    app.setup()
    sys.exit(app.exec_())     
