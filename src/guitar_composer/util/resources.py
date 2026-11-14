import os
from pathlib import Path 


def get_custom_instruments_filename():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filename = str(Path( Path(base_data_dir) / "instruments" / "customInstruments.json"  ))
    return filename

def get_instruments_filename():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filename = str(Path( Path(base_data_dir) / "sf_info" / "instruments.json"  ))
    return filename

def get_instrument_groupings_filename():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filename = str(Path( Path(base_data_dir) / "instruments" / "groupings.json"  ))
    return filename

def get_effects_config_filename():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filename = str(Path( Path(base_data_dir) / "effect_config" / "config.json" ))
    return filename

def get_drum_groups_filename():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filename = str(Path(base_data_dir) / "midi_drum_groups.json")
    return filename

def get_ladspa_filespec():
    base_plugin_dir = os.environ.get('LADSPA_PATH', str(Path("usr/lib/ladspa")))
    filespec = str(Path(base_plugin_dir) / "*.so")
    return filespec

def get_soundfont_filespec():
    base_data_dir = os.environ.get('GC_DATA_DIR',str(Path.home() / ".guitar-composer" / "data" ))
    filespec = str(Path(base_data_dir) / "sf" / "*")
    return filespec
