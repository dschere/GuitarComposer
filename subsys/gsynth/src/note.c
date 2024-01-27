#include "note.h"
#include "app.h"
#include "cmd.h"
#include "ff_evt.h"

#include <fluidsynth.h>


#define STACCATO_DYN_INC 5
#define NUM_BEND_STEPS 13
#define PB_MIN 0
#define PB_MIDVAL 8192
#define PB_MAX 8192 * 2


static int perform_hand_effects(
    struct Cmd* cmd, struct App* app, struct Note* nptr
) {
    int err = 0;
    int i;
    float m = (cmd->staccato == 1) ? 0.75: 1.0;
    int millisecs_for_entire_note = 1000 * m * (nptr->duration * (60.0 / app->bpm));
    int millsecs_per_ev = millisecs_for_entire_note / (1 + nptr->he.num_ev);  
    int key = nptr->key;
    int ms = 0;
    int b_ev_tm;
    // pitch bend range: (0-16383 with 8192 being center)
    int pb_val = PB_MIDVAL;
    int pb_inc;

    for(i = 0; i < nptr->he.num_ev; i++) {
        switch(nptr->he.ev_list[i].ev_type) {
            case EV_HAMMERON:
                
                future_noteoff(app, nptr->gstr, key, 
                    ms + millsecs_per_ev - 1);

                key = app->tuning[nptr->gstr] + nptr->he.ev_list[i].val;
                future_noteon(app, nptr->gstr, key, cmd->dynamic, 
                    ms + millsecs_per_ev );

                ms += millsecs_per_ev;

                // if legato is not set and this is the last hammer on
                // we should schedule a noteoff event  
                if (cmd->legato == 0 && i == (nptr->he.num_ev - 1))  {
                    future_noteoff(app, nptr->gstr, key, 
                        ms + millsecs_per_ev - 1);        
                }
                
                break;
            case EV_PREBEND_RELEASE:
                nptr->he.ev_list[i].val *= -1;
                // drop through and do the bend logic.
            case EV_BEND:  
                // pitch bend range: (0-16383 with 8192 being center)
                // compute 13 events over 1/2 of the duration.
                pb_inc = (PB_MIDVAL * (nptr->he.ev_list[i].val / 8.0))/NUM_BEND_STEPS;
                for(i = 0; i < NUM_BEND_STEPS; i++) {
                    // 13 events to create a smooth bend 
                    ms += millsecs_per_ev / (NUM_BEND_STEPS * 2);
                    // make sure the new value is legal.
                    if (
                        ((pb_val + pb_inc) < PB_MAX) &&
                        ((pb_val + pb_inc) > 0)
                    ) { 
                        pb_val += pb_inc;
                        future_bend(app, nptr->gstr, pb_val, ms);
                    }
                }
                break;
            case EV_SLIDE:
                break;
            case EV_VIBRATO:
                break;
        }
    }

    if (pb_val != PB_MIDVAL) {

    }

    return err;
}

/*
create a premivite that schedules events

noteon
noteoff
pitch bend
*/
int note_proc(
    struct Note* nptr, 
    struct Cmd* cmd, 
    struct App* app
) {
    int err = 0;
    int key = app->tuning[nptr->gstr] + nptr->fret; // use tuning to determine midi key
    int dyn = cmd->dynamic;
    // convert bpm to beats per second, determine the duration in seconds
    // for the note then convert to milliseconds.
    int ms_dur = 1000 * (nptr->duration * (60.0 / app->bpm));

    if (cmd->staccato == 1) {
        if (127 > (dyn + STACCATO_DYN_INC)) {
            dyn += STACCATO_DYN_INC;
        }
    }

    // Is there currently a note playing on this string (legato) ?
    if (app->gstring_state[nptr->gstr] != GSTR_NOT_PLAYING) {
        fluid_synth_pitch_bend(app->synth, nptr->gstr, 0); // zero out any pitch bend.
        fluid_synth_noteoff(app->synth, nptr->gstr, app->gstring_state[nptr->gstr]);
    }

    // play noteon immediately, if staccato add a little volume to make the 
    // note stand out more
    fluid_synth_noteon(app->synth, nptr->gstr, key, dyn);

    // schedule the noteoff if legato is not set.
    if (cmd->legato == 0) {
        if (cmd->staccato == 1) {
            // we are directed to play 75% duration then insert a rest for
            // the remaining 25%
            future_noteoff(app, nptr->gstr, key, (int) ms_dur * 0.75);
        } else {
            future_noteoff(app, nptr->gstr, key, ms_dur);
        }
    }

    // handle hand effects such as hammer ons and bends etc.
    if (nptr->he.num_ev > 0) {
        if ((err = perform_hand_effects(cmd, app, nptr)) != 0) {
            return err;
        }
    }

    // record string state so we can perform a noteoff if the string is
    // still playing.
    app->gstring_state[nptr->gstr] = key;

    return err;
}
