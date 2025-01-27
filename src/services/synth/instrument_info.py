import os
import glob
import re
import json

pattern = "([0-9]+)-([0-9]+) ([^\n]+)"
select_parser = re.compile(pattern)

"""
Creates a structure as follows

sfpaths = [... list of sound font files ...]
instruments = [{
    sfont_id: ..
    sf_filename: ...
    instruments: [{
        bank_num,
        preset_num,
        name
    }]
}]
"""


class instrument_spec:
    def __init__(self):
        self.name = None
        self.sf_filename = None
        self.sfont_id = -1
        self.bank_num = -1
        self.preset_num = -1


class instrument_info:
    prefered_font = "27mg_Symphony_Hall_Bank.SF2"

    def find(self, name):
        return self.prefered.get(name, self.lookup.get(name))

    def __init__(self):
        script = os.environ['GC_BASE_DIR']+"/scripts/print_instrument_info.sh"
        sf_dir = os.environ['GC_DATA_DIR']+"/sf"
        sf_info_file = os.environ['GC_DATA_DIR']+"/sf_info/instruments.json"
        self.sfpaths = glob.glob(sf_dir+"/*")
        self.instruments = []

        # give preference to this sound font

        self.prefered = {}
        # all others
        self.lookup = {}

        sfont_id = 0
        for sf_filename in [f.split("/")[-1] for f in self.sfpaths]:
            script = os.environ['GC_BASE_DIR'] + \
                "/scripts/print_instrument_info.sh"
            cmd = "%s %s" % (script, sf_filename)
            sfont_id += 1
            sf_info = {
                "sfont_id": sfont_id,
                "sf_filename": sf_filename,
                "instruments": []
            }
            for line in os.popen(cmd).readlines():
                m = select_parser.match(line)
                if m:
                    spec = instrument_spec()
                    spec.sfont_id = sfont_id
                    spec.sf_filename = sf_filename
                    spec.name = m.group(3)
                    spec.bank_num = int(m.group(1))
                    spec.preset_num = int(m.group(2))

                    if sf_filename == self.prefered_font:
                        self.prefered[spec.name] = spec
                    else:
                        self.lookup[spec.name] = spec

                    sf_info["instruments"].append({
                        "bank_num": int(m.group(1)),
                        "preset_num": int(m.group(2)),
                        "name": m.group(3)
                    })
            self.instruments.append(sf_info)

        f = open(sf_info_file, "w")
        f.write(json.dumps(self.instruments, indent=4, sort_keys=True))
        f.close()
