#!/usr/bin/env python

import os
import glob
from setuptools import setup, find_packages, Extension, find_namespace_packages
from setuptools.command.build_py import build_py


import sys
import subprocess

current_module_path = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
BASE_DIR = "."
PACKAGES = "glib-2.0 sdl2 gmodule-2.0"

# added packages libavformat-dev libavcodec-dev libavutil-dev libc6-dev

_include_dirs = ['src/cmodules/gcsynth/', f'{BASE_DIR}/include']
_libraries = ['m','ev']
_library_dirs = [f'{BASE_DIR}/lib64']

glib_include = subprocess.getoutput(
    f"pkg-config --cflags-only-I {PACKAGES}").split()
glib_libs = subprocess.getoutput(f"pkg-config --libs {PACKAGES}").split()

# pkg-config libs/inculdes
_include_dirs += [path[2:] for path in glib_include]  # Removing '-I' prefix
_libraries += [lib[2:]
               for lib in glib_libs if lib.startswith('-l')]
# Removing '-L' prefix
_library_dirs += [lib[2:] for lib in glib_libs if lib.startswith('-L')]


GCSYNTH_CSOURCES = [
    'src/cmodules/gcsynth/gcsynth.c',
    'src/cmodules/gcsynth/gcsynth_start.c',
    'src/cmodules/gcsynth/gcsynth_stop.c',
    'src/cmodules/gcsynth/gcsynth_filter.c',
    'src/cmodules/gcsynth/gcsynth_channel.c',
    'src/cmodules/gcsynth/gcsynth_event.c',
    'src/cmodules/gcsynth/pyutil.c',
    'src/cmodules/gcsynth/gcsynth_sf.c',
    'src/cmodules/gcsynth/gcsynth_acapture.c',
    'src/cmodules/gcsynth/ringbuffer.c',
    'src/cmodules/gcsynth/repeater_loop.c',
    'src/cmodules/gcsynth/fgraph/freqdomain.c',
    'src/cmodules/gcsynth/fgraph/mixer.c',
    'src/cmodules/gcsynth/fgraph/splitter.c',
    'src/cmodules/gcsynth/fgraph/effect.c',
    'src/cmodules/gcsynth/fgraph/gainbalance.c',
    'src/cmodules/gcsynth/fgraph/bandpass.c',
    'src/cmodules/gcsynth/fgraph/fgraph.c',
    'src/cmodules/gcsynth/fgraph/fgrun.c',
    'src/cmodules/gcsynth/fgraph/py_graph_api.c'
]

# Define the extension module with the extra include and library directories
gcsynth_module = Extension(
    'guitar_composer.gcsynth',
    sources=GCSYNTH_CSOURCES,
    include_dirs=_include_dirs,  # Include path
    library_dirs=_library_dirs,  # Library path
    libraries=_libraries,     # Link against packages
    extra_compile_args=['-g3'],
#    extra_compile_args=['-O3','-g'],  # Add the -g2 flag for debug symbols
    # Ensure the linker also gets the debug symbols
    extra_link_args={'win32':[]}.get(sys.platform, ['-lasound'])
)

# Helper to automatically grab all files in the directory
def get_data_files():
    data_files = []
    for root, dirs, files in os.walk('data'):
        if files:
            # Maps (target_installation_directory, [list_of_source_files])
            data_files.append((root, [os.path.join(root, f) for f in files]))
    return data_files

setup(
    name="guitar_composer",
    version="0.1.0",
    # Tells setuptools that all packages live under the src directory
    package_dir={"": "src"},
    # Automatically finds all Python packages inside the src directory
    packages=find_namespace_packages(where="src"),
    # Defines and builds your C extension module
    ext_modules=[
        gcsynth_module
    ],
    #packages=["guitar_composer"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
    ],
    python_requires=">=3.7",
    data_files=get_data_files(),
)

