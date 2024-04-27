from .measure_divider import measure_divider

from guitarcomposer.ui.config import config

class tableture_measure_divider(measure_divider):
    def __init__(self, linetype):
        super().__init__(config().tablature_item, linetype)   


