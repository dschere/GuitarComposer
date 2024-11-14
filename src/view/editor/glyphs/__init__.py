""" 
    layout = QGridLayout()
    layout.setHorizontalSpacing(0)

    layout.addWidget(glyphs.StaffHeaderGlyph(glyphs.TREBLE_CLEFF,"Eb","4/4",120), 0, 0)
    layout.addWidget(glyphs.StaffGlyph(), 0, 1)

    t = glyphs.TabletureGlyph()
    layout.addWidget(t, 1, 1)

    layout.addWidget(glyphs.EffectsGlyph(True), 2, 1)

    #t.setCursor(1, 13)
    t.set_cursor(1)
    #t.set_tab_note(1, 13)
    t.set_tab_note(2, 12)
"""

from .common import TREBLE_CLEFF, BASS_CLEFF, DRUM_CLEFF
from .staff import StaffHeaderGlyph, StaffGlyph
from .tableture import TabletureGlyph
