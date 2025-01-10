""" 

In the case of a change in duration, a deletion or a cut and paste workflow
the entire track needs to be recalculated from the point where the change 
occured.


"""

from view.editor.sequenceRenderer import SequenceRenderer
from models.track import TabEvent, StaffEvent, MeasureEvent

def recalculateSequence(renderer: SequenceRenderer, moment: int):
    """ 
    Case 1: deletion.
        moment -> the moment before the deletion 
                  (implies that the first tab event can't be deleted)

    Case 2: duration change
        moment -> the moment of the TabEvent being changed.
                        
    """
    # get grid column associated with this moment
    model = renderer.get_model()
    editor = renderer.get_editor() 
    col = model.moment_pres_column[moment]

    seq = model.getSequence()
    staff_event = seq.getActiveStaff(model.getMoment())
    (measure_moment, measure_event) = \
        seq.search(model.getMoment(), seq.BACKWARD, seq.MEASURE_EVENT)
    current_moment = model.getMoment()

    ts = staff_event.compute_timespec()  # type: ignore
    beats_in_measure = ts.beats_per_measure * ts.beat_duration

    te = model.getTabEvent()
    new_te = te.clone()
    
    
    







