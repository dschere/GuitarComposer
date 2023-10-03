import os


# If the environment variable is not defined deduce the directory
# from the location of this module.
module_dir = os.path.dirname(os.path.abspath(__file__))
default_dir = module_dir+"/../../data/"

DATA_DIR=os.environ.get("GC_DATA_DIRECTORY",default_dir)
if DATA_DIR[-1] != "/":
    DATA_DIR += "/"

PRESET_DIR=DATA_DIR+"presets/"
LIVEAUDIO_DIR=DATA_DIR+"liveaudio/"

os.system("mkdir -p %s" % PRESET_DIR)
os.system("mkdir -p %s" % LIVEAUDIO_DIR)



