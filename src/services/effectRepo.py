import glob
from typing import List
import gcsynth
import os
from models.effect import Effect, Effects
import json
from singleton_decorator import singleton
import copy

EFFECT_CFG_FILE = os.environ['GC_DATA_DIR']+"/effect_config/config.json"
LADSPA_FILE_SPEC = os.environ.get('LADSPA_PATH','/usr/lib/ladspa')+"/*.so"

@singleton
class EffectRepository:

    def get(self, name) -> Effect | None:
        return self.effects.get(name)

    def getNames(self) -> List[str]:
        return list(self.effects.keys())
    
    def update(self, elist: List[Effect]):
        data = open(EFFECT_CFG_FILE).read()
        cfg = json.loads(data)
        for e in elist:
            cfg[e.label] = e.json_data()
        data = json.dumps(cfg, indent=4, sort_keys=True)
        open(EFFECT_CFG_FILE,"w").write(data)

    def create_effects(self) -> Effects:
        """
        Return a set of effects that have been selected
        from a pool of ladspa plugins. Each is initialized 
        to disabled and with default values.
        """    
        r = Effects()
        for (label, e) in self.effects.items():
            if e.selected:
                r.add(label, copy.deepcopy(e))
        return r

    def __init__(self):
        cfg = {}
        self.effects = {}
        
        if os.access(EFFECT_CFG_FILE, os.F_OK):
            data = open(EFFECT_CFG_FILE).read()
            cfg = json.loads(data)
        
        ladspa_labels = set()

        for filepath in glob.glob(LADSPA_FILE_SPEC):
            for data in gcsynth.ladspa_plugin_labels(filepath):
                t = data.split(':')
                label = t[0]
                name = t[1]
                ladspa_labels.add(label)
                # newly detected effect
                if label not in cfg:
                    controls = gcsynth.filter_query(filepath, label)
                    e = Effect(name, label, filepath, controls)
                    cfg[label] = {
                        'controls': controls,
                        'name': name,
                        'label': label,
                        'selected': False,
                        'path': filepath
                    }
                    self.effects[label] = e
                else:
                    # previously loaded
                    d = cfg[label]
                    controls = d['controls']
                    e = Effect(name, label, filepath, controls)
                    e.selected = d['selected']
                    self.effects[label] = e

        data = json.dumps(cfg, indent=4, sort_keys=True)
        open(EFFECT_CFG_FILE,"w").write(data)
               
        # there is a chance that the user may delete a ladspa audio effect
        # from teh system, then we would have a stale entry in our database.
        deleted_effects = set()       
        for label in self.effects.keys():
            if label not in ladspa_labels:
                deleted_effects.add(label)

        for label in deleted_effects:
            if label in self.effects:
                del self.effects[label]



def unittest():
    er = EffectRepository()
    print(er.getNames())
    e = er.get("butthigh_iir")
    assert(e)
    er.update(e)
        
if __name__ == '__main__':
    unittest()