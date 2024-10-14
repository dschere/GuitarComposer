"""
In addition to the QStyle which supports CSS theming of Qt widgets 
I have variables that are used for teh various drawings that take place in
the app. To support theming in the future these configuration could be
grouped as associated with a theme. 

The class names here match the class names they provide styling information
for.
"""


class _GuitarFretboardStyle:
    # silver
    string_color_rgb = (192, 192, 192)
    # copper
    fret_color_rgb = (184, 115, 51)
    # burgundy
    fretboard_bg_color_rgb = (128, 0, 32)   
    # gold
    orament_color_rgb = (255, 235, 14) 
    # red
    text_color_rgb = (255, 0, 0)
    # onyx
    background_color_rgb = (53, 57, 53)


GuitarFretboardStyle = _GuitarFretboardStyle()    
