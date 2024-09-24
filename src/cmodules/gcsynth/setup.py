from setuptools import setup, Extension
import os
import subprocess

current_module_path = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
BASE_DIR=current_module_path+"/../../.."

PACKAGES = "glib-2.0"

_include_dirs = ['.',f'{BASE_DIR}/include']
_libraries    = ['fluidsynth']
_library_dirs = [f'{BASE_DIR}/lib64']

glib_include = subprocess.getoutput(f"pkg-config --cflags-only-I {PACKAGES}").split()
glib_libs = subprocess.getoutput(f"pkg-config --libs {PACKAGES}").split()

# pkg-config libs/inculdes
_include_dirs += [path[2:] for path in glib_include]  # Removing '-I' prefix
_libraries    += [lib[2:] for lib in glib_libs if lib.startswith('-l')]  # Removing '-l' prefix
_library_dirs += [lib[2:] for lib in glib_libs if lib.startswith('-L')]  # Removing '-L' prefix


CSOURCES = [
    'gcsynth.c',
    'voice_data_router.c',
    'gcsynth_start.c',
    'gcsynth_stop.c',
    'gcsynth_filter.c'
]

# Define the extension module with the extra include and library directories
gcsynth_module = Extension(
    'gcsynth',
    sources=CSOURCES,
    include_dirs=_include_dirs,  # Include path
    library_dirs=_library_dirs,  # Library path
    libraries   =_libraries,     # Link against packages
)

# Setup the module
setup(
    name='gcsynth',
    version='1.0',
    description='A Python C extension module for gcsynth',
    ext_modules=[gcsynth_module],
)
