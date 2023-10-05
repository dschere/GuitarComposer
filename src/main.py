#!/usr/bin/env python3

import os
import sys
import logging

# setup formatting for logger
def setup_logger():
    fmt = "%(asctime)s %(thread)d %(filename)s:%(lineno)d %(levelname)s\n`"
    fmt += "- %(message)s"
    loglevel = os.environ.get("LOGLEVEL","DEBUG")
    if not hasattr(logging,loglevel):
        print("Warning: undefined LOGLEVEL '%s' falling back to DEBUG!" % loglevel)
        loglevel = 'DEBUG'      
    logging.basicConfig(stream=sys.stdout,
        format=fmt,
        level=getattr(logging,loglevel)
    )
setup_logger()


# Get the directory of the current module
module_dir = os.path.dirname(os.path.abspath(__file__))

# set basepath for module imports
sys.path.append(module_dir)

from ui.mainwin import mainloop

# start application
mainloop()


