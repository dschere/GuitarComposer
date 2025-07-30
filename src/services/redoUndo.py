import os
from PyQt6.QtCore import QObject
from singleton_decorator import singleton
from models.track import Track
from view.events import Signals

import uuid
import pickle
import atexit

CHANGE_PATH_SPEC = "/tmp/gc-edit-"

def recursive_diff(obj1, obj2, visited=None):
    if visited is None:
        visited = set()

    # Handle identical objects (to prevent infinite recursion)
    if id(obj1) == id(obj2):
        return {}

    # Add current objects to visited set
    if (id(obj1), id(obj2)) in visited:
        return {} # Already compared this pair, avoid circular reference
    visited.add((id(obj1), id(obj2)))

    # Handle different types
    if type(obj1) != type(obj2):
        return {"type_mismatch": (type(obj1).__name__, type(obj2).__name__)}

    # Handle primitive types and non-object types directly
    if not hasattr(obj1, '__dict__'):
        return obj2 if obj1 != obj2 else {}

    diffs = {}
    # Compare attributes
    for key in obj1.__dict__:
        if key not in obj2.__dict__:
            diffs[key] = {"removed": getattr(obj1, key)}
        else:
            val1 = getattr(obj1, key)
            val2 = getattr(obj2, key)
            if hasattr(val1, '__dict__') and hasattr(val2, '__dict__'):
                # Recursively compare nested objects
                nested_diff = recursive_diff(val1, val2, visited)
                if nested_diff:
                    diffs[key] = nested_diff
            elif val1 != val2:
                diffs[key] = {"changed": (val1, val2)}

    # Check for attributes present in obj2 but not obj1
    for key in obj2.__dict__:
        if key not in obj1.__dict__:
            diffs[key] = {"added": getattr(obj2, key)}

    return diffs


class track_change_entry:
    """
    just keep adding history redo is diabled, undo enabled
    history = [c1, c2, c3] 
                        ^
                       current

                   << undo
                   >> redo     

    history = [c1, c2, c3]  use does an undo
                   ^
                  current

                  redo can take us back to c3 unless
                  there is a change, if a change then
                  [c1,c2,c4] with c4 being current                 
    """

    def filename(self):
        r = str(uuid.uuid4())
        # unique to track and current change
        return f"{CHANGE_PATH_SPEC}{id(self.track)}-{r}"

    def update(self, track: Track):
        "if strack changed save changes"
        potential_new = pickle.dumps(track)
        # MODEL_UPDATE will cause potential_new == self.current 
        if potential_new != self.current:
            new = potential_new
            fn = self.filename()
            with open(fn, 'wb') as file:
                file.write(new)
            self.current = new
            if self.index == len(self.history):
                self.history.append(fn)
                self.index += 1
            else:
                self.history[self.index] = fn
                self.history = self.history[:self.index+1] 
            
    def undo(self) -> Track | None:
        result = None
        if self.index > 0:
            self.index -= 1
            fn = self.history[self.index]
            self.current = open(fn,'rb').read()
            result = pickle.loads(self.current)
             
        return result

    def redo(self) -> Track | None:
        result = None
        if (self.index+1) < len(self.history):
            self.index += 1
            fn = self.history[self.index]
            self.current = open(fn,'rb').read()
            result = pickle.loads(self.current) 

        return result


    def __init__(self, track: Track):
        self.track = track
        self.changed = False
        self.current = pickle.dumps(None)
        # list of change filenames generated of songs.
        self.history = []
        self.index = 0 

@singleton
class RedoUndoProcessor(QObject):
    """
    Keeps track of changes with the current track being edited. Each track is associated
    with list of changes, the most recent is kept in memory the rest are cached to the temp
    directory as pickled objects.
    """
    def undo(self, track: Track) -> Track | None:
        entry = self.track_table.get(track.track_edit_id)
        if entry is not None:
            return entry.undo()     

    def redo(self, track: Track) -> Track | None:
        entry = self.track_table.get(track.track_edit_id)
        if entry is not None:
            return entry.redo()

    def update(self, track: Track) -> None:
        assert(track.track_edit_id != "")
        if track.track_edit_id not in self.track_table:
            self.track_table[track.track_edit_id] = track_change_entry(track)
        else:
            # add to track history
            self.track_table[track.track_edit_id].update(track)

    def disable_updates(self):
        Signals.redo_undo_update.disconnect(self.update)

    def enable_updates(self):
        Signals.redo_undo_update.connect(self.update)

    def on_exit(self):
        os.system(f"rm -f {CHANGE_PATH_SPEC}* > /dev/null &")
        
    def __init__(self):
        super().__init__()
        self.track_table = {}
        self.model_update_in_process = False
        Signals.redo_undo_update.connect(self.update)

        atexit.register(self.on_exit)

    