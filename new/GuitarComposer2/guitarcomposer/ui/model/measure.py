
# here for historical purposes until deleted.
# the measure is too inter dependant on a track
# if the moment in music changes for a note due to
# a new note being inserted before a note on the 
# the tablature then all notes that follow must change.

# thus a measure can't be represented by an object it
# is simply a book keeping artificat. Its just tracks containing
# a list of notes.

"""
import copy
from .note import note

class measure:
    def __init__(self, timesig = (4,4) ):
        # either notes/rests or chords
        self.moments = []
        self.max_beats = timesig[0] / (timesig[1]/4)
        
        # book keeping variables
        self.beats_used = 0.0
    
        
        
    # -- these routines maniuplate the self.momemts 
    #    each returns the number of beats left to complete
    #    the measure. A negative number indicates an overflow.
    #    in which the note_model duration is altered to fit the
    #    the measure and new note model is created with a duration
    #    of the overflow so it can be used as the first note of 
    #    the next measure.
        
    def append_note(self, note_model):
        note_duration = note_model.duration
        new_note = None
                
        if self.beats_used + note_duration < self.max_beats:
            self.beats_used += note_duration
        else:
            new_dur = self.max_beats - self.beats_used
            new_note_dur = (self.beats_used+note_dur) - self.max_beats
            
            # alter duration
            note_model.duration = new_dur
            # make a copy 
            new_note = copy.copy( note_model )
            new_note.duration =  new_note_dur
            
        self.moments.append(note_model)
        return new_note      
    
    def insert_note(self, note_model, beat):
        pass
"""    
    
