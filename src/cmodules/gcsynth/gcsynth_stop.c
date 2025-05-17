#include "gcsynth.h"

#include "gcsynth_sf.h"

void gcsynth_stop(struct gcsynth* gcSynth)
{
    gcsynth_sf_shutdown();
}
