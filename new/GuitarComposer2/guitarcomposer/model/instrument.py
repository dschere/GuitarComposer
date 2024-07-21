

from guitarcomposer.common.midi_instrument_codes import REALISTIC_GUITAR

class instrument:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'undefined')
        self.midi_program = kwargs.get('pgm', REALISTIC_GUITAR)
        self.name = kwargs.get('name','noname')
