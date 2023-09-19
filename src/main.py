#!/usr/bin/env python3

import os
import sys

# Get the directory of the current module
module_dir = os.path.dirname(os.path.abspath(__file__))

# set basepath for module imports
sys.path.append(module_dir)

from ui.mainwin import mainloop

# start application
mainloop()


