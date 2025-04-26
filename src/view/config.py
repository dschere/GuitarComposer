"""
In addition to the QStyle which supports CSS theming of Qt widgets
I have variables that are used for teh various drawings that take place in
the app. To support theming in the future these configuration could be
grouped as associated with a theme.

The class names here match the class names they provide styling information
for.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from singleton_decorator import singleton
#from attic.new.GuitarComposer2.guitarcomposer.common.durationtypes import SIXTEENTH, \
#    THIRTYSECOND, SIXTYFORTH

PRESETS_TEXT = "presets"

BEND_LINE_COLOR = (240, 234, 214)
BEND_ZERO_PITCH_LINE_COLOR = (128, 0, 32)
BEND_GRID_LINE_COLOR = (255, 235, 14)
BEND_POINT_COLOR = (0, 255, 255)
BEND_GROUP_TEXT = "Pitch Bend Control"
BEND_RANGE_TEXT = "Pitch in range in steps"

@singleton
class _GuitarFretboardStyle:
    # silver
    string_color_rgb = (192, 192, 192)
    # copper
    fret_color_rgb = (184, 115, 51)
    # burgundy
    fretboard_bg_color_rgb = (128, 0, 32)
    # gold
    orament_color_rgb = (255, 235, 14)
    # egg shell
    text_color_rgb = (240, 234, 214)
    # onyx
    background_color_rgb = (53, 57, 53)
    # cyan
    scale_root_color_rgb = (0, 255, 255)
    # navy
    scale_color_rgb = (0, 0, 128)
    # purple
    note_press = (255, 0, 255)
    # bright red
    error = (255, 0, 0)


@singleton
class EditorKeyMap:
    WHOLE_NOTE = ord('w')
    HALF_NOTE = ord('h')
    QUARTER_NOTE = ord('q')
    EIGHT_NOTE = ord('e')
    SIXTEENTH_NOTE = ord('s') 
    THRITY_SECOND_NOTE = ord('T')
    SIXTY_FORTH_NOTE = ord('S')

    dur_lookup = {
        WHOLE_NOTE: 4.0,
        HALF_NOTE: 2.0,
        QUARTER_NOTE: 1.0,
        EIGHT_NOTE: 0.5,
        SIXTEENTH_NOTE: 0.25,
        THRITY_SECOND_NOTE: 0.125,
        SIXTY_FORTH_NOTE: 0.0625
    }

    # hittng . or ; twice clears them
    DOTTED_NOTE = ord('.')
    DOUBLE_DOTTED_NOTE = ord(';')
    TRIPLET_NOTES = ord('t')
    QUINTUPLIT_NOTES = ord('Q')
    REST = ord('r')

    START_REPEAT = ord('[')
    END_REPEAT = ord(']')

    LAGATO = ord('~')
    STACATTO = ord('`')

    BEND = ord('b')
    SLIDE = ord('/')
    VIBRATO = ord('v')

    def isEditorInput(self, event: QKeyEvent):
        result = True
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            result = False
        elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
            result = False

        return result


@singleton
class _LabelText:
    # TODO, tie into localization so these can be switched.
    properties = "properties"
    title = "title"
    track = "track"

    filter_instruments = "Filter instruments:"
    filter_scale = "Filter scales:"
    scales = "Scales:"
    instruments = "Instruments:"
    keys = "Keys:"
    scale_selector_group = "Fretboard Overlay"
    clear_scale = "Clear"
    nav_track_properties = "Track properties"
    add_track = "Add Track"
    tuning = "Tuning"
    


GuitarFretboardStyle = _GuitarFretboardStyle()
LabelText = _LabelText()

ORAGANIZATION = "OneManShow Enterprises"
APP_NAME = "GuitarComposer"
