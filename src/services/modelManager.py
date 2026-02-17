"""
Manage an archive of models. There is a master index file that maps the
preset name to a file containing a serialized model. The user may change the preset 
resulting in a re-index. 
"""
import os 
import pickle
from typing import Dict, List
import uuid

from singleton_decorator import singleton

from models.filterGraph import FilterGraph
from models.song import Song
from view.events import Signals




class ManifestEntry:
    def __init__(self):
        # The title of a song, the preset name of a 
        # set of effects etc.
        self.tag_name = ""
        self.file_name = ""
        self.class_name = ""
        self.uuid = ""
        

class Manifest:
    """
    A data structure that holds references to serialized modules.
    """
    def __init__(self):
        self.index : Dict[str, ManifestEntry] = {}
        self.map_tag_name_to_uuid : Dict[str, str] = {}

    def getPresets(self) -> List[str]:
        r = []
        for entry in self.index.values():
            if entry.class_name != "FilterGraph":
                continue
            r.append(entry.tag_name)
        return r
    
    def getSongTitles(self):
        r = []
        for entry in self.index.values():
            if entry.class_name != "Song":
                continue
            r.append(entry.tag_name)
        return r
    

    def update_name(self, model : Song | FilterGraph):
        # find the old name 
        uuid = model.uuid
        entry = self.index[uuid]
        self.add_model(model)
        # remove old tag_name
        del self.map_tag_name_to_uuid[entry.tag_name]


    def add_model(self, model : Song | FilterGraph):
        """ 
        Add a filter graph or song to the manifest.
        """
        entry = ManifestEntry()
        entry.class_name = model.__class__.__name__
        if isinstance(model, Song):
            s : Song = model
            entry.tag_name = s.title
            entry.file_name = s.filename
            entry.uuid = s.uuid
        elif isinstance(model, FilterGraph):
            fg : FilterGraph = model
            entry.tag_name = fg.preset
            entry.file_name = fg.filename
            entry.uuid = fg.uuid
        else:
            raise TypeError("Expected Song or FilterGraph model")
        self.map_tag_name_to_uuid[entry.tag_name] = entry.uuid
        self.index[entry.uuid] = entry

    def lookup_filename(self, tag_name):
        d = self.map_tag_name_to_uuid
        if tag_name in d:
            uuid = d[tag_name]
            return self.index[uuid].file_name
        return None

    def remove_model(self, tag_name):
        d = self.map_tag_name_to_uuid
        if tag_name in d:
            uuid = d[tag_name]
            del self.index[uuid]
            del d[tag_name]


@singleton
class ModelManager:

    def __init__(self):
        self.model_dir = os.environ['GC_DATA_DIR']+os.sep+"models"
        self.manifest = Manifest() 

        if not os.access(self.model_dir, os.F_OK):
            os.mkdir(self.model_dir)
        self.manifest_file = self.model_dir+os.sep+"manifest.dat"
        if os.access(self.manifest_file, os.F_OK):
            with open(self.manifest_file, 'rb') as f:
                self.manifest = pickle.load(f)


    def get_presets(self) -> List[str]:
        return self.manifest.getPresets()

    def get_songs(self) -> List[str]:
        return self.manifest.getSongTitles()

    def get_model(self, tag_name) -> Song | FilterGraph | None:
        file_name = self.manifest.lookup_filename(tag_name)
        if file_name is None:
            return None
        with open(file_name, 'rb') as f:
            return pickle.load(f)


    def add_model(self, model : Song | FilterGraph):
        filename = self.model_dir+os.sep+model.__class__.__name__+'_'+model.uuid+'.dat'
         
        if isinstance(model, Song):
            s : Song = model
            s.filename = filename
            if s.title == "":
                raise TypeError("Unable to save a song with a blank title")
        elif isinstance(model, FilterGraph):
            fg : FilterGraph = model
            fg.filename = filename
            if fg.preset == "":
                raise TypeError("Unable to save a filter graph with a blank preset name")
        else:
            raise TypeError("Expected Song or FilterGraph model")
        
        with open(model.filename, 'wb') as f:
            pickle.dump(model, f)

        self.manifest.add_model(model)
        with open(self.manifest_file, 'wb') as f:
            pickle.dump(self.manifest, f)

    def remove_model(self, tag_name):
        filename = self.manifest.lookup_filename(tag_name)
        if filename is None:
            return
        os.remove(filename)
        self.manifest.remove_model(tag_name)
        with open(self.manifest_file, 'wb') as f:
            pickle.dump(self.manifest, f)
        





