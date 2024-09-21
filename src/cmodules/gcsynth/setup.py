from setuptools import setup, Extension
import os

current_module_path = os.sep.join(os.path.abspath(__file__).split(os.sep)[:-1])
BASE_DIR=current_module_path+"/../../.."

# Define the extension module with the extra include and library directories
gcsynth_module = Extension(
    'gcsynth',
    sources=['gcsynth.c','voice_data_router.c'],
    include_dirs=['.',f'{BASE_DIR}/include'],  # Include path
    library_dirs=[f'{BASE_DIR}/lib64'],     # Library path
    libraries=['fluidsynth'],                                   # Link against fluidsynth
)

# Setup the module
setup(
    name='gcsynth',
    version='1.0',
    description='A Python C extension module for gcsynth',
    ext_modules=[gcsynth_module],
)
