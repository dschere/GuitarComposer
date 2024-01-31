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

//#define DEBUG 1

static int perform_hand_effects(
    struct Cmd* cmd, struct App* app, struct Note* nptr
) {
    int err = 0;
    int i;
    float m = (cmd->staccato == 1) ? 0.75: 1.0;
    int millisecs_for_entire_note = 1000 * m * (nptr->duration * (60.0 / app->bpm));
    int millsecs_per_ev = millisecs_for_entire_note / (1 + nptr->he.num_ev);  
    int key = nptr->key;
    int ms = nptr->delay;
    int b_ev_tm;
    // pitch bend range: (0-16383 with 8192 being center)
    int pb_val = PB_MIDVAL;
    int pb_inc;
    float semitones;
    int end_value_of_pb; 
    int new_key;

    for(i = 0; i < nptr->he.num_ev; i++) {
        switch(nptr->he.ev_list[i].ev_type) {
            case EV_HAMMERON:
                
                future_noteoff(app, nptr->gstr, key, 
                    ms + millsecs_per_ev - 1);

                key = app->tuning[nptr->gstr] + nptr->he.ev_list[i].val;
                future_noteon(app, nptr->gstr, key, cmd->dynamic, 
                    ms + millsecs_per_ev );

                ms += millsecs_per_ev;

                break;
            case EV_PREBEND_RELEASE:
                nptr->he.ev_list[i].fval *= -1;
                // drop through and do the bend logic.
            case EV_BEND:  
                // pitch bend range: (0-16383 with 8192 being center)
                // this number represents the number of semitones from 0-12
                // 1. compute semitiones
                semitones = nptr->he.ev_list[i].fval;
                // 2. compute the ending value of the bend movement.
                end_value_of_pb =  semitones * (PB_MIDVAL / PITCHWHEEL_SENSITIVITY_IN_SEMITONES);
                // 3. compute the increment of 13 movements to create a smooth bend.
                pb_inc = end_value_of_pb / NUM_BEND_STEPS;

                for(i = 0, b_ev_tm = ms; i < NUM_BEND_STEPS; i++) {
                    // 13 events to create a smooth bend 
                    b_ev_tm += millsecs_per_ev / (NUM_BEND_STEPS * 2);
                    // make sure the new value is legal.
                    if (
                        ((pb_val + pb_inc) < PB_MAX) &&
                        ((pb_val + pb_inc) > 0)
                    ) { 
                        pb_val += pb_inc;
                        future_bend(app, nptr->gstr, pb_val, b_ev_tm);
                    }
                }
                ms += millsecs_per_ev;
                break;
            case EV_SLIDE:
                // 1. compute the number of semitones from the current key to the desired one
                new_key = app->tuning[nptr->gstr] + nptr->he.ev_list[i].val;
                semitones = new_key - key;
                // 2. compute the ending value of the bend movement.
                end_value_of_pb =  semitones * (PB_MIDVAL / PITCHWHEEL_SENSITIVITY_IN_SEMITONES);
                // 3. compute the increment of 13 movements to create a smooth bend.
                pb_inc = end_value_of_pb / NUM_BEND_STEPS;

                // the pacing is faster for the slide, the movement happens in 1/4
                // of the allocated time.
                for(i = 0, b_ev_tm = ms; i < NUM_BEND_STEPS; i++) {
                    // 13 events to create a smooth bend 
                    b_ev_tm += millsecs_per_ev / (NUM_BEND_STEPS * 4);
                    // make sure the new value is legal.
                    if (
                        ((pb_val + pb_inc) < PB_MAX) &&
                        ((pb_val + pb_inc) > 0)
                    ) { 
                        pb_val += pb_inc;
                        future_bend(app, nptr->gstr, pb_val, b_ev_tm);
                    }
                }
                ms += millsecs_per_ev;
                break;
            case EV_VIBRATO:
                break;
        }

        // if legato is not set and this is the last hammer on
        // we should schedule a noteoff event  
        if (cmd->legato == 0 && i == (nptr->he.num_ev - 1))  {
            future_noteoff(app, nptr->gstr, key, 
                ms + millsecs_per_ev - 1);        
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

#ifdef DEBUG
printf("note_proc gstr=%d fret=%d millisec dur=%d",
    nptr->gstr, nptr->fret, ms_dur);
#endif


    if (cmd->staccato == 1) {
        if (127 > (dyn + STACCATO_DYN_INC)) {
            dyn += STACCATO_DYN_INC;
        }
    }

    // Is there currently a note playing on this string (legato) ?
    if (app->gstring_state[nptr->gstr] != GSTR_NOT_PLAYING) {
        //fluid_synth_pitch_bend(app->synth, nptr->gstr, PB_MIDVAL); // zero out any pitch bend.
        future_bend(app, nptr->gstr, PB_MIDVAL, 0);
        //fluid_synth_noteoff(app->synth, nptr->gstr, app->gstring_state[nptr->gstr]);
        future_noteoff(app, nptr->delay, key, nptr->delay);
    }

    // play noteon immediately, if staccato add a little volume to make the 
    // note stand out more
    //fluid_synth_noteon(app->synth, nptr->gstr, key, dyn);
    future_noteon(app, nptr->gstr, key, dyn, nptr->delay);

    // schedule the noteoff if legato is not set.
    if (cmd->legato == 0) {
        if (cmd->staccato == 1) {
            // we are directed to play 75% duration then insert a rest for
            // the remaining 25%
            future_noteoff(app, nptr->gstr, key, (int) ms_dur * 0.75);
        } else {
            future_noteoff(app, nptr->gstr, key, ms_dur);
        }
        future_bend(app, nptr->gstr, PB_MIDVAL, ms_dur);
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
