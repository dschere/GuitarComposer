"""
Creates the data directory is it doesn't exist or if the version
file changes. 

If the GC_DATA_DIR is not defined then we default to a directory under home.

"""
import os 
import pathlib
import shutil

import guitar_composer
from guitar_composer.util.setenv import setenv


GC_DATA_DIR = 'GC_DATA_DIR'


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

    try:
        gc_mod_path = pathlib.Path(list(guitar_composer.__path__)[0])
    except:
        gc_mod_path = pathlib.Path(guitar_composer.__file__) # type: ignore
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
