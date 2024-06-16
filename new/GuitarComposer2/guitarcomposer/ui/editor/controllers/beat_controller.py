"""

Ensures alignment of beats.

The track with the largest width to hold all the note events
determines the width of a measure.



for each beat determine the track with the smallest duration
  this is used to fill the width for a given beat.
  
  
Example:
  s -> sixteenth second note
  q -> quater note
  . -> blank glyps
  
-------------------
track 1:   q....  
-------------------
track 2:   sssss   
  

    

"""

from PyQt6.QtWidgets import QWidget, QGridLayout


class beat_controller:
    def __init__(self, grid_layout, ):
        self.grid_layout = grid_layout

