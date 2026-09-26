"""
Creates the data directory is it doesn't exist or if the version
file changes. 

If the GC_DATA_DIR is not defined then we default to a directory under home.

"""
import os 
from pathlib import Path
from guitar_composer.util.setenv import setenv
import shutil



ENVVAR_GC_DATA_DIR = 'GC_DATA_DIR'


def get_data_dir() -> Path:
    """
    If the GC_DATA_DIR environment variable is set, use that as the data directory, otherwise
    default to a directory under the user's home directory.
    """
    default_data_dir = Path.home() / ".guitar-composer" / "data"
    return Path(os.environ.get(ENVVAR_GC_DATA_DIR, default_data_dir))


def get_current_data_dir_version(data_dir: Path) -> int:
    """
    get the current installed version of the data directory. If the version file doesn't exist, return 0. 
    """
    initfile = data_dir / "__init__.py"
    if initfile.exists():
        exec(open(initfile).read())
        if 'VERSION' in locals():
            return locals()['VERSION']
    return 0 
    

def setup_application_data():
    """
    Setup data directory if it doesn't exist or if the version file changes. 
    In the case of the former we create the directory and copy the baseline data files. 
    In the case of the latter we merge the baseline data files into the existing directory.
    """
    import guitar_composer.data as gc_data
    data_dir = get_data_dir()
    if not data_dir.exists():
        print(f"setup_application_data: Creating data directory at {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
        baseline_data_dir = Path(gc_data.__file__).parent
        shutil.copytree(baseline_data_dir, data_dir, dirs_exist_ok=True)
    if get_current_data_dir_version(data_dir) < gc_data.VERSION:
        print(f"setup_application_data: Updating data directory at {data_dir} to version {gc_data.VERSION}")
        baseline_data_dir = Path(gc_data.__file__).parent
        shutil.copytree(baseline_data_dir, data_dir, dirs_exist_ok=True)

    if ENVVAR_GC_DATA_DIR not in os.environ:
        from guitar_composer.util.setenv import setenv
        setenv(ENVVAR_GC_DATA_DIR, str(data_dir))
        


def unittest():
    if ENVVAR_GC_DATA_DIR in os.environ:
        del os.environ[ENVVAR_GC_DATA_DIR]
    setup_application_data()

    
if __name__ == '__main__':
    unittest()
