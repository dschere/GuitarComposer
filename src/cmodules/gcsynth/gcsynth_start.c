#include <unistd.h>
#include <stdio.h>

#include "gcsynth.h"
#include "gcsynth_event.h"
#include "gcsynth_sf.h"
#include "gcsynth_channel.h"


void gcsynth_start(struct gcsynth* gcSynth)
{
#define RAISE(errmsg) { gcsynth_raise_exception(errmsg); gcsynth_stop(gcSynth); return; }   
    int i;
    char errmsg[4096];
    struct gcsynth_cfg* cfg = &gcSynth->cfg;

    // check for existance of soundfont files 
    for(i = 0; i < cfg->num_sfpaths; i++) {
        if (access(cfg->sfpaths[i],F_OK) != 0) {
            sprintf(errmsg,"Soundfont file (%s) not found!",cfg->sfpaths[i]);
            RAISE(errmsg)
        }
    }

    // new synth
    if (gcsynth_sf_init(cfg->sfpaths, cfg->num_sfpaths, synth_filter_router)) {
        RAISE("unable to launch synth")
    }

    gcsynth_sequencer_setup(gcSynth);
}

