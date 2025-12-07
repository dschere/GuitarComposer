from typing import List, Tuple
from singleton_decorator import singleton
import json
import os 


@singleton
class DrumDatabase:
    def __init__(self):
        dbfile = os.environ['GC_DATA_DIR']+os.sep+"midi_drum_groups.json"
        self.data = json.loads(open(dbfile).read())

    def getDrumInfoFromMidicode(self, midi_code) -> None | Tuple[str, str, int]:
        if midi_code == -1: 
            return

        for group_name, v in self.data.items():
            for (idx, (midi_key_code, desc)) in enumerate(v):
                if v == midi_code:
                    return (group_name, desc, idx)
                    
    def groups(self) -> List[str]:
        r =  list(self.data.keys())
        r.sort()
        return r  

    def drumData(self, group_name) -> List[Tuple[int, str]]:
        return [(midi_key_code, desc) for (midi_key_code, desc) in self.data[group_name]]
            



