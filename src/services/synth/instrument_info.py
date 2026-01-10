import os
import glob
import re
import json
import sys


class instrument_spec:
    def __init__(self):
        self.name = None
        self.sf_filename = None
        self.sfont_id = -1
        self.bank_num = -1
        self.preset_num = -1
        self.type = ""


class instrument_info:
    prefered_font = "27mg_Symphony_Hall_Bank.SF2"

    def find(self, name):
        return self.prefered.get(name, self.default_data.get(name))
    

    def classify(self, gset, spec: instrument_spec):
        group_name = "other"
        for g in self.group_spec['groups']:
            exclude_list = g.get('exclude_string',[])
            match_list = g.get('match_string',[])

            excluded = False
            for token in exclude_list:
                if token in spec.name:
                    excluded = True
                    break 

            if not excluded:
                for token in match_list:
                    if token in spec.name:
                        group_name = g['name']
                        iset = gset.get(group_name,set())
                        iset.add(spec.name)
                        gset[group_name] = iset 
                        return
                
        gset[group_name].add(spec.name)
        

    def setup(self):
        sf_info_file = os.environ['GC_DATA_DIR']+"/sf_info/instruments.json"
        if not os.access(sf_info_file,os.F_OK):
            raise RuntimeError("instrument info file missing is gcsyth running?")
        
        gset = {
            'other': set()
        }

        sf_info_list = json.loads(open(sf_info_file).read())
        for sf_info in sf_info_list:
            sf_filename = sf_info['sf_filename']
            sfont_id = sf_info['sfont_id']
            # fill either the prefered 
            table = self.prefered if self.prefered_font in sf_filename else self.default_data 
            
            for instrument_data in sf_info['instruments']:
                spec = instrument_spec()
                spec.preset_num = instrument_data['preset_num']
                spec.name = instrument_data['name']
                spec.bank_num = instrument_data['bank_num']
                spec.sf_filename = sf_filename
                spec.sfont_id = sfont_id

                table[spec.name] = spec

                # find group classification
                self.classify(gset, spec)

            self.instruments.append(sf_info)

        for gname, iset in gset.items():
            instr_list = list(iset)
            instr_list.sort() 
            self.groups[gname] = instr_list


    def instrumentGroups(self):
        return self.groups
            
    def __init__(self):
        sf_dir = os.environ['GC_DATA_DIR']+"/sf"
        self.sfpaths = glob.glob(sf_dir+"/*")

        self.instruments = []

        # give preference to this sound font
        self.prefered = {}
        # all others
        self.default_data = {}
        self.groups = {}

        ins_group_file = os.environ['GC_DATA_DIR']+"/instruments/groupings.json"
        self.group_spec = json.loads(open(ins_group_file).read())
