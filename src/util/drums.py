from typing import List, Tuple
from singleton_decorator import singleton
import json
import os 


@singleton
class DrumDatabase:
    def __init__(self):
        dbfile = os.environ['GC_BASE_DIR']+os.sep+"midi_drum_groups.json"
        self.data = json.loads(dbfile)

    def groups(self) -> List[str]:
        return list(self.data.keys())  

    def drumData(self, group_name) -> List[Tuple[int, str]]:
        return [(midi_key_code, desc) for (midi_key_code, desc) in self.data[group_name]]
            



