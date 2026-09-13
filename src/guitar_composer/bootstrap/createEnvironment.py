"""
Creates the data directory is it doesn't exist or if the version
file changes. 

If the GC_DATA_DIR is not defined then we default to a directory under home.

"""
import sys
import os 
import pathlib
import shutil

import guitar_composer
from guitar_composer.util.setenv import setenv


GC_DATA_DIR = 'GC_DATA_DIR'



def get_imported_module_path(module) -> str:
    """Safely extracts the absolute path from an already imported module object.
    Once upon a time in python you could get the path just like 
    this <module>.__file__ ... now look at this BULLSHIT!
    """
    # 1. Fallback for frozen/compiled binaries where internal paths are stripped
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        # If it's a package/directory inside the executable folder
        module_name = getattr(module, '__name__', '')
        possible_dir = os.path.join(exe_dir, module_name)
        if os.path.isdir(possible_dir):
            return possible_dir

    # 2. Check __file__ (Standard for .py files and standard packages)
    # We use getattr and verify it's a string, protecting against missing/None values
    file_attr = getattr(module, '__file__', None)
    if isinstance(file_attr, str) and file_attr:
        # Filter out 'frozen' placeholder strings used by some compilers
        if file_attr != 'frozen':
            return os.path.abspath(file_attr)

    # 3. Check __path__ (Standard for Namespace packages or packages missing __file__)
    path_attr = getattr(module, '__path__', None)
    if path_attr:
        try:
            # __path__ is an iterable (usually an _NamespacePath or list)
            first_path = list(path_attr)[0]
            if isinstance(first_path, str) and first_path:
                return os.path.abspath(first_path)
        except (IndexError, TypeError):
            pass

    # 4. Final safety net using its spec blueprint if available
    spec = getattr(module, '__spec__', None)
    if spec is not None:
        if spec.origin and isinstance(spec.origin, str) and spec.origin != 'frozen':
            return os.path.abspath(spec.origin)
        if spec.submodule_search_locations:
            try:
                first_loc = list(spec.submodule_search_locations)[0]
                return os.path.abspath(first_loc)
            except (IndexError, TypeError):
                pass

    raise ValueError(f"Could not safely determine path for module: {getattr(module, '__name__', 'unknown')}")



def merge_directories(source_dir, destination_dir):
    """
    Platform-neutral way to merge source contents into destination.
    Overwrites conflicting files/directories and preserves unique destination files.
    """
    # Using Path objects ensures cross-platform path handling (Windows/macOS/Linux)
    src = pathlib.Path(source_dir)
    dst = pathlib.Path(destination_dir)
    
    # dirs_exist_ok=True allows merging into an existing target folder
    shutil.copytree(src, dst, dirs_exist_ok=True)


def set_gc_directory():
    if GC_DATA_DIR in os.environ and os.access(os.environ[GC_DATA_DIR],os.F_OK):
        gc_data_dir = os.environ[GC_DATA_DIR]
    else:
        home_dir_parts = list(pathlib.Path(os.environ['HOME']).parts) 
        default_dir_parts = home_dir_parts + [".guitar-composer","data"]
        gc_data_dir = str(pathlib.Path(*default_dir_parts))
    return gc_data_dir

def get_gc_data_version(gc_data_dir):
    parts = list(pathlib.Path(gc_data_dir).parts) + ["version.txt"]
    version_path = str(pathlib.Path(*parts))
    if os.access(version_path, os.F_OK):
        version = float(open(version_path).read())
    else:
        version = 0.0
    return version

def get_baseline_data_dir():
    """
    Go into the distribution, the setuptools has placed collection of baseline data
    files such as sound fonts, presets etc.  
    """
    import guitar_composer

    gc_mod_path = pathlib.Path(get_imported_module_path(guitar_composer))
    parts = list(gc_mod_path.parts[:-2]) + ['data']
    return str(pathlib.Path(*parts))


def setup_application_data():
    gc_data_dir = set_gc_directory()
    baseline_data_dir = get_baseline_data_dir()

    existing_schema_version = get_gc_data_version(gc_data_dir)
    baseline_schema_version = get_gc_data_version(baseline_data_dir)

    if baseline_schema_version > existing_schema_version:
        print(f"Updating data directory {gc_data_dir} to latest version {baseline_schema_version}")
        merge_directories(baseline_data_dir, gc_data_dir)

    setenv(GC_DATA_DIR, gc_data_dir)
    os.environ[GC_DATA_DIR] = gc_data_dir



def unittest():
    del os.environ['GC_DATA_DIR']
    setup_application_data()

    
if __name__ == '__main__':
    unittest()
