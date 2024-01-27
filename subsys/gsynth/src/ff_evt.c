#include <stdio.h>
#include <stdarg.h>

#include "ff_evt.h"

#include <fluidsynth.h>


enum
{
   FF_EVT_NOTEON,
   FF_EVT_NOTEOFF,
   FF_EVT_PITCHWHEEL
};




static int future_fluid_evt(int evt_code, struct App* app, ...)
{
    va_list args;
    int chan;
    short key;
    int vel;
    int when;
    int val;

    // schedule note off for current key
    fluid_event_t * ev = new_fluid_event();

    fluid_event_set_source(ev, -1);
    fluid_event_set_dest(ev, app->synth_destination);

    va_start(args, app);
    
    switch(evt_code) {
        case FF_EVT_NOTEON:
            if ((chan = va_arg(args, int)) == -1) return -1;
            if ((key  = va_arg(args, int)) == -1) return -1;
            if ((vel  = va_arg(args, int)) == -1) return -1;
            if ((when = va_arg(args, int)) == -1) return -1;

            fluid_event_noteon(ev, chan, key, vel);
            break;
        case FF_EVT_NOTEOFF:
            if ((chan = va_arg(args, int)) == -1) return -1;
            if ((key  = va_arg(args, int)) == -1) return -1;
            if ((when = va_arg(args, int)) == -1) return -1;

            fluid_event_noteoff(ev, chan, key);
            break;
        case FF_EVT_PITCHWHEEL:
            if ((chan = va_arg(args, int)) == -1) return -1;
            if ((val  = va_arg(args, int)) == -1) return -1;
            if ((when = va_arg(args, int)) == -1) return -1;
            
            fluid_event_pitch_bend(ev, chan, val);
            break;    
        default:
            fprintf(stderr,"Invalid event %d\n", evt_code); 
            return -1;
    }

    fluid_sequencer_send_at(app->sequencer, ev, when, 0);
    delete_fluid_event(ev);

    return 0;
}


int future_noteon(struct App* app, int chan, int key, int vel, int when) {
    return future_fluid_evt(FF_EVT_NOTEON, app, chan, key, vel, when);
}
int future_noteoff(struct App* app, int chan, int key, int when) {
    return future_fluid_evt(FF_EVT_NOTEOFF, app, chan, key, when);
}
int future_bend(struct App* app, int chan, int val, int when) {
    return future_fluid_evt(FF_EVT_PITCHWHEEL, app, chan, val, when);
}



