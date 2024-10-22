#!/usr/bin/env python

import os, glob

script = os.environ['GC_BASE_DIR']+"/scripts/print_instrument_info.sh"
sf_dir = os.environ['GC_DATA_DIR']+"/sf"
sf_filenames = [f.split("/")[-1] for f in glob.glob(sf_dir+"/*")]

print(sf_filenames)
print(script)