"""
In addition to the QStyle which supports CSS theming of Qt widgets
I have variables that are used for teh various drawings that take place in
the app. To support theming in the future these configuration could be
grouped as associated with a theme.

The class names here match the class names they provide styling information
for.
"""
from singleton_decorator import singleton


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


GuitarFretboardStyle = _GuitarFretboardStyle()
LabelText = _LabelText()

ORAGANIZATION = "OneManShow Enterprises"
APP_NAME = "GuitarComposer"
