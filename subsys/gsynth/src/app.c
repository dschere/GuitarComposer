#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fluidsynth.h>

#include "app.h"
#include "cmd.h"


int App_mainloop(struct App* app)
{
    struct Cmd c;
    int i;

    app->sequencer = new_fluid_sequencer2(0);
    /* register the synth with the sequencer */
    app->synth_destination = fluid_sequencer_register_fluidsynth(
        app->sequencer, app->synth);
    /* register the client name and callback */
    app->client_destination = fluid_sequencer_register_client(
        app->sequencer, "gsynth", NULL, NULL);

    app->bpm = DEFAULT_BPM;    
    for(i = 0; i < NUM_GSTRINGS; i++) {
        // value is the current key playing or -1
        app->gstring_state[i] = GSTR_NOT_PLAYING; 
    }
    

    while(1) {
        memset(&c, 0, sizeof(c)); 
        if (Cmd_from_stdin(&c)) {
            break; // error reading from stdin
        }

        if (strcmp(c.command,"quit") == 0) {
            break; // graceful shutdown.
        }    

        if (Cmd_dispatch(&c, app) == -1) {
            break; // fatal error
        }
    }

    return 0;
}

int App_setup(struct App* app)
{
    int err = FLUID_OK;
    int i;

    memset(app, 0, sizeof(struct App));  
    app->duration_multiplier = 1.0;
    app->settings = NULL;
    app->synth = NULL;
    app->adriver = NULL;

    /* Create the settings object. This example uses the default
     * values for the settings. */
    app->settings = new_fluid_settings();
    if(app->settings == NULL)
    {
        fprintf(stderr, "Failed to create the settings\n");
        err = 2;
        goto cleanup;
    }

    /* Create the synthesizer */
    app->synth = new_fluid_synth(app->settings);
    if(app->synth == NULL)
    {
        fprintf(stderr, "Failed to create the synthesizer\n");
        err = 3;
        goto cleanup;
    }

    err = fluid_settings_setstr(app->settings, "audio.driver", "alsa");
    if (err != FLUID_OK) {
        printf("Unable to use alsa audio driver!\n");
        goto cleanup;
    }

    // soundfont containing each string guage.
    app->font_id = fluid_synth_sfload(app->synth, app->soundfontpath, 1);
    if (app->font_id == FLUID_FAILED) {
        fprintf(stderr,"Unable to load %s\n", app->soundfontpath);
        goto cleanup;
    }

    app->adriver = new_fluid_audio_driver(app->settings, app->synth);

    for(i = 0; i < NUM_GSTRINGS; i++) {
        // the instrument code matches the channel number for 0-5
        if (fluid_synth_program_change(app->synth, i, i) == FLUID_FAILED) {
            fprintf(stderr,"Unable to assign instrument %d to channel %d\n", i, i);
            goto cleanup;
        }
        fluid_synth_pitch_wheel_sens(app->synth,i,PITCHWHEEL_SENSITIVITY_IN_SEMITONES);
        
        //TODO add harmoics to the sound font
    }

    // set default tuning
    app->tuning[0] = 40;
    app->tuning[1] = 45;
    app->tuning[2] = 50;
    app->tuning[3] = 55;
    app->tuning[4] = 59;
    app->tuning[5] = 64;

    
    
    // ready to receive commands ...    
    return 0;

cleanup:

    if(app->adriver)
    {
        delete_fluid_audio_driver(app->adriver);
    }

    if(app->synth)
    {
        delete_fluid_synth(app->synth);
    }

    if(app->settings)
    {
        delete_fluid_settings(app->settings);
    }

    return err;
}

void App_schedule_noteon(struct App* app, int chan, short key, short vel, unsigned int ticks)
{
    fluid_event_t *ev = new_fluid_event();
    fluid_event_set_source(ev, -1);
    fluid_event_set_dest(ev, app->synth_destination);
    fluid_event_noteon(ev, chan, key, vel);
    fluid_sequencer_send_at(app->sequencer, ev, ticks, 1);
    delete_fluid_event(ev);
}

