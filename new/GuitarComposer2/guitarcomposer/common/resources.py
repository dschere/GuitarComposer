import os
import guitarcomposer

RootDirectory = os.sep.join(guitarcomposer.__file__.split(os.sep)[:-2])

FLUID_SYNTH_SCRIPT = RootDirectory + os.sep + "scripts" + os.sep + "miditrackplayer.sh"
GUITAR_SOUND_FONT  = RootDirectory + os.sep + "data" + os.sep + "sf" + os.sep + "guitar-per-string.sf2"
DEFAULT_SOUND_FONT = RootDirectory + os.sep + "data" + os.sep + "sf" + os.sep + "27mg_Symphony_Hall_Bank.SF2"

