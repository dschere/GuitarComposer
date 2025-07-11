"""
Displays a single TabEvent as in multiple rows.

The first row is the staff were it is presented as music
notation. The next row is the ornement row which can show
things like stacatto or legato. The next row is the
tableature row which contains the guitar tab. 

Below that will be the effects row that will allow for
effect changes.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout)
from models.measure import Measure, TabEvent

from view.editor import glyphs 
from models.track import Track
from PyQt6.QtCore import Qt
from view.editor.glyphs.common import STAFF_SYM_WIDTH


class TabEventPresenter(QWidget):

    def set_string(self, string):
        self.tab_event.string = string

    def get_string(self):
        return self.tab_event.string

    def __init__(self, tab_event: TabEvent, measure: Measure, track: Track):
        super().__init__()

        self.tab_event = tab_event
        # allow for navigation within the measure <-- -->
        self.prev : TabEventPresenter | None = None
        self.next : TabEventPresenter | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)


        staff_presentation      = glyphs.StaffGlyph(self.tab_event, measure, track)
        ornamental_presentation = glyphs.oramental_markings(self.tab_event)
        tab_presentation        = glyphs.TabletureGlyph(self.tab_event)
        effects_presentation    = glyphs.EffectsGlyph(self.tab_event)

        #TODO fix this crap!
        # setSpacing does not work! I needed this kluge to force 
        # a blank widget to eat up any extra padding set to exactly the correct
        # height so that no padding is rendered between widgets.
        pad = QWidget()
        pad.setFixedHeight(170)
        pad.setFixedWidth(STAFF_SYM_WIDTH)
        #################################### 

        layout.addWidget(staff_presentation, alignment=Qt.AlignmentFlag.AlignTop )
        layout.addWidget(ornamental_presentation )
        layout.addWidget(tab_presentation )
        layout.addWidget(effects_presentation)
        layout.addWidget(pad)

        self.setLayout(layout)

        self.staff_p = staff_presentation
        self.ornamental_p = ornamental_presentation
        self.tab_p = tab_presentation
        self.effects_p = effects_presentation

    def set_play_line(self):
        self.staff_p.set_play_line()
        self.update()

    def clear_play_line(self):
        self.staff_p.clear_play_line() 
        self.update()

    def beat_overflow_error(self):
        self.staff_p.beat_overflow_error()    

    def beat_underflow_error(self):
        self.staff_p.beat_underflow_error()    

    def clear_beat_error(self):
        self.staff_p.clear_beat_error()

    def cursor_on(self):
        self.tab_p.set_cursor(self.tab_event.string)

    def cursor_off(self):
        self.tab_p.clear_cursor()

    def cursor_up(self):
        # Up arrow pressed and move the cursor up or loop around
        self.tab_event.string = \
            (self.tab_event.string - 1) % len(self.tab_event.fret)
        self.tab_p.set_cursor(self.tab_event.string)

    def cursor_down(self):
        # Down arrow pressed and move the cursor up or loop around
        self.tab_event.string = \
            (self.tab_event.string + 1) % len(self.tab_event.fret)
        self.tab_p.set_cursor(self.tab_event.string)

    def set_fret(self, fret_value):
        # Number pressed, update the fret value
        self.tab_event.fret[self.tab_event.string] = fret_value
        self.tab_p.set_tab_note(self.tab_event.string, fret_value)

    def clear_fret(self):
        self.set_fret(-1)


if __name__ == '__main__':
    from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTabWidget,
    QWidget, QSplitter, QStatusBar, QVBoxLayout, 
    QMenuBar, QMenu
    )
    import qdarktheme
    
    t = Track() 
    (te, measure) = t.current_moment()
    assert(te)

    import sys
    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    window = TabEventPresenter(te, measure, t)

    window.cursor_on()
    window.cursor_up()
    window.beat_overflow_error()
    
   
    window.show()
    sys.exit(app.exec())




        
