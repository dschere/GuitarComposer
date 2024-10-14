import os
import glob
import re

pattern = "([0-9]+)-([0-9]+) ([^\n]+)"
select_parser = re.compile(pattern) 

"""
Creates a structure as follows

sfpaths = [... list of sound font files ...]
instruments = [{
    instr_id: ..
    sf_filename: ...
    instruments: [{
        bank_num,
        preset_num,
        name
    }]
}]
"""
class instrument_info:
    def __init__(self):
        script = os.environ['GC_BASE_DIR']+"/scripts/print_instrument_info.sh"
        sf_dir = os.environ['GC_DATA_DIR']+"/sf"
        self.sfpaths = glob.glob(sf_dir+"/*")
        self.instruments = []

        instr_id = 0
        for sf_filename in [f.split("/")[-1] for f in self.sfpaths]:
            script = os.environ['GC_BASE_DIR']+"/scripts/print_instrument_info.sh"
            cmd = "%s %s" % (script, sf_filename)
            instr_id += 1
            sf_info = {
                "instr_id": instr_id,
                "sf_filename": sf_filename,
                "instruments": []
            }
            for line in os.popen(cmd).readlines():
                m = select_parser.match(line)
                if m:
                    sf_info["instruments"].append({
                        "bank_num": int(m.group(1)),
                        "preset_num": int(m.group(2)),
                        "name": m.group(3)     
                    })
            self.instruments.append(sf_info)    



    